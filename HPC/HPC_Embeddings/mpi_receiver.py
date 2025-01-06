from mpi4py import MPI
import threading
import queue
import json
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from pathlib import Path
import signal
import sys

@dataclass
class Section:
    act_title: str
    reg_title: str
    title: str
    content: str
    url: str
    section_url: str
    section_id: str
    section_number: str
    source_rank: int
    timestamp: str = None

class MPIReceiver:
    def __init__(self, output_dir="section_data"):
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        self.running = True
        self.sections = []  # General list of sections, not per rank
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Separate buffers for each rank
        self.sections_by_rank = {0: [], 1: []}  # Initialize with ranks expected to send data
        self.section_count_by_rank = {0: 0, 1: 0}  # Counter for each rank
        self.total_count = 0

        # Signal handling
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

        print(f"Python receiver initialized with rank {self.rank} of {self.size}")
        sys.stdout.flush()

    def receive_data(self):
        """Threaded data reception with non-blocking MPI."""
        while self.running:
            try:
                status = MPI.Status()
                self.comm.probe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
                source = status.Get_source()
                tag = status.Get_tag()

                # Receive length
                length = np.zeros(1, dtype=np.int32)
                self.comm.Recv([length, 1, MPI.INT], source=source, tag=tag)

                # Receive JSON data
                buffer = bytearray(length[0])
                self.comm.Recv([buffer, MPI.BYTE], source=source, tag=tag)

                # Parse JSON and enqueue
                data = json.loads(buffer.decode('utf-8'))
                section = Section(**data)
                self.queue.put(section)
            except Exception as e:
                print(f"Error receiving data: {e}")
                
    def receive_section(self):
        try:
            status = MPI.Status()
            self.comm.probe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)

            # Check for termination tag (99)
            if status.Get_tag() == 99:
                print(f"Received termination signal from rank {status.Get_source()}")
                termination_msg = bytearray(100)  # Match the size of MPISection content field
                self.comm.Recv([termination_msg, 100, MPI.CHAR], source=status.Get_source(), tag=99)
                termination_str = termination_msg.decode('utf-8').strip()
                if termination_str == "END_OF_TRANSMISSION":
                    print("End of transmission received.")
                    self.running = False
                return None

            # For regular messages
            length = np.zeros(1, dtype=np.int32)
            self.comm.Recv([length, 1, MPI.INT], source=status.Get_source(), tag=0)

            json_buffer = bytearray(length[0])
            self.comm.Recv([json_buffer, length[0], MPI.CHAR], source=status.Get_source(), tag=1)
            json_str = json_buffer.decode('utf-8')
            data = json.loads(json_str)

            # Parse the Section object and tokens
            section = Section(
                act_title=data.get('act_title', ''),
                reg_title=data.get('reg_title', ''),
                title=data.get('title', ''),
                content=data.get('content', ''),
                url=data.get('url', ''),
                section_url=data.get('section_url', ''),
                section_id=data.get('section_id', ''),
                section_number=data.get('section_number', ''),
                source_rank=data.get('source_rank', -1),
                timestamp=datetime.now().isoformat()
            )

            tokens = data.get('tokens', [])
            token_chunks = data.get('token_chunks', [])  # Extract token chunks
            print(f"Received section: {section.title} with {len(tokens)} tokens and {len(token_chunks)} chunks")

            return section, tokens, token_chunks
        except Exception as e:
            print(f"Error receiving section: {e}")
            return None, None, None

        
    def handle_shutdown(self, signum, frame):
        print(f"\nReceived signal {signum}, saving data and shutting down...")
        self.save_batch()
        self.running = False
        sys.exit(0)

    def process_data(self):
        """Process data from the queue."""
        while self.running or not self.queue.empty():
            try:
                section = self.queue.get(timeout=1)
                # Save or process the section
                print(f"Processing section: {section.title}")
                # Save or batch as needed
            except queue.Empty:
                continue
                
    def save_batch(self, rank):
        """Save sections, their tokens, and token chunks from a specific rank"""
        sections_with_tokens = self.sections_by_rank.get(rank, [])
        if not sections_with_tokens:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rank_{rank}_batch_{self.section_count_by_rank[rank]}.json"
        output_path = self.output_dir / filename

        data = {
            'metadata': {
                'source_rank': rank,
                'total_processed': self.section_count_by_rank[rank],
                'sections_in_batch': len(sections_with_tokens),
                'timestamp': timestamp
            },
            'sections': []
        }

        for section, tokens, token_chunks in sections_with_tokens:
            section_dict = asdict(section)
            section_dict['tokens'] = tokens  # Add tokens to the section data
            section_dict['token_chunks'] = token_chunks  # Add token chunks to the section data
            data['sections'].append(section_dict)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(sections_with_tokens)} sections from rank {rank} to {output_path}")
        self.sections_by_rank[rank] = []  # Clear after saving

    def run(self):
        try:
            while self.running:
                section, tokens, token_chunks = self.receive_section()
                if section is None:  # Termination or error
                    break

                source_rank = section.source_rank
                if source_rank in self.sections_by_rank:
                    # Store section, tokens, and chunks
                    self.sections_by_rank[source_rank].append((section, tokens, token_chunks))
                    self.section_count_by_rank[source_rank] += 1
                    self.total_count += 1

                    # Save if batch size reached for this rank
                    if len(self.sections_by_rank[source_rank]) >= 1000:
                        self.save_batch(source_rank)

                    if self.total_count % 100 == 0:
                        print(f"Total processed: {self.total_count} "
                              f"(Rank 0: {self.section_count_by_rank[0]}, "
                              f"Rank 1: {self.section_count_by_rank[1]})")
                else:
                    print(f"Unexpected rank {source_rank} received, ignoring...")
        except KeyboardInterrupt:
            print("Interrupted by user")
        finally:
            # Save remaining sections for all ranks
            for rank in self.sections_by_rank.keys():
                self.save_batch(rank)

def main():
    receiver = MPIReceiver()
    if receiver.rank == 2:  # Dedicated receiver process
        receiver.run()

if __name__ == "__main__":
    main()
