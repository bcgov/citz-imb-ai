# Documentation: Murmur3-Powered Hash Table for WordPiece Tokenization

## 1. Overview

This document provides a detailed explanation of the custom hash table implementation used in the `HPCChain` pre-processing engine. This hash table is the backbone of the WordPiece tokenizer, serving as the vocabulary that maps sub-word strings to their corresponding integer token IDs.

Its performance is critical; every word is broken down by repeatedly querying this table. To achieve the required speed, the implementation uses the high-performance **Murmur3** hashing algorithm and resolves collisions with separate chaining. Furthermore, the search function is accelerated with **AVX-512 SIMD instructions** to speed up string comparisons in the rare event of a hash collision.

---

## 2. Why Murmur3?

The choice of a hashing algorithm is crucial for the performance of a hash table. A poor algorithm leads to many "collisions" (multiple keys hashing to the same table slot), which degrades lookup performance from nearly instantaneous (O(1)) to the speed of a linear search (O(n)). We use Murmur3 because it excels in several key areas:

#### a. Excellent Distribution (Avalanche Effect)
Murmur3 has a fantastic "avalanche effect," meaning that a tiny change in the input key (like changing a single character) results in a drastically different, seemingly random output hash. This ensures that similar strings (e.g., "token", "tokens", "##token") are spread evenly across the hash table's slots, minimizing collisions.

#### b. High Performance
Murmur3 is designed to be fast, especially on modern x86 architectures. It processes data in 4-byte chunks and uses a series of multiplication and bitwise rotation operations that are very efficient for CPUs to execute.

#### c. Simplicity and Non-Cryptographic Nature
For a hash table, we don't need the security guarantees of a cryptographic hash function like SHA-256. Cryptographic hashes are intentionally slow to compute to resist brute-force attacks. Murmur3 is a **non-cryptographic** hash, meaning it's optimized purely for speed and distribution, making it a perfect fit for this use case.

---

## 3. Implementation Details

The hash table is implemented as an array of "slots" or "buckets," where each slot can point to a linked list of entries. This method of handling collisions is known as **separate chaining**.

### a. The Hash Function (`MurmurHash3`)

The core of the system is the `MurmurHash3` function, a well-known public domain algorithm.

```c
// A wrapper around MurmurHash3 to provide a consistent seed.
uint32_t hash_function(const char *key) {
    // The seed (0x9747b28c) is a fixed, arbitrary number to initialize the hash.
    return MurmurHash3(key, strlen(key), 0x9747b28c);
}
```

When a key (a sub-word string) needs to be stored or found, `hash_function` is called. The resulting 32-bit hash is then mapped to a slot in the table using the modulo operator: `slot = hash % table->size`.

### b. Data Structures

```c
// A single key-value pair in the hash table.
typedef struct Entry {
    char *key;
    char *value; // Token ID is stored as a string
    struct Entry *next; // Pointer to the next entry in case of a collision
} Entry;

// The main hash table structure.
typedef struct HashTable {
    Entry **entries; // An array of pointers to Entry structs
    size_t size;     // The total number of slots in the table
} HashTable;
```

### c. Core Operations (`insert` and `search`)

**Insertion (`insert`):**
1.  The `key` is hashed to determine its slot.
2.  The code checks if an entry already exists at that slot.
3.  If the slot is empty, a new `Entry` is created and placed there.
4.  If the slot is not empty (a collision), the code traverses the linked list at that slot.
    * If an entry with the same key is found, its value is updated.
    * If the end of the list is reached, the new entry is appended.

**Search (`search` with SIMD):**
The search operation is where performance is most critical.
1.  The `key` is hashed to find the correct slot.
2.  The code traverses the linked list at that slot.
3.  For each entry in the list, instead of using the standard `strcmp`, it uses our custom **`simd_strcmp`**.

### d. SIMD-Accelerated String Comparison

In the rare event of a hash collision, we must compare the search key against the keys in the linked list. For long strings, `strcmp` can be slow as it compares byte-by-byte. Our `simd_strcmp` function uses AVX-512 to compare strings in 64-byte chunks.

```c
static inline int simd_strcmp(const char *s1, const char *s2) {
    // ...
    // Load 64 bytes from each string into AVX-512 registers
    __m512i chunk1 = _mm512_loadu_si512((const __m512i *)s1);
    __m512i chunk2 = _mm512_loadu_si512((const __m512i *)s2);

    // Compare the chunks byte by byte in a single instruction
    __mmask64 cmp_mask = _mm512_cmpeq_epi8_mask(chunk1, chunk2);

    // If all 64 bytes are not equal, find the first difference
    if (cmp_mask != 0xFFFFFFFFFFFFFFFF) {
        // ... find and return the difference
    }
    // ... continue to the next 64-byte chunk
}
```
This provides a significant speedup for the string comparison part of the lookup process, ensuring that even in the face of collisions, performance remains high.

---

## 4. Role in WordPiece Tokenization

The hash table is the engine that drives the `get_token` function in the WordPiece algorithm. The process works as follows:

1.  The `get_token` function receives a word (e.g., "tokenization").
2.  It enters a loop, attempting to find the longest possible prefix of that word in the vocabulary.
3.  It does this by repeatedly calling `search(table, ...)`:
    * `search(table, "tokenization")` -> Fails
    * `search(table, "tokenizatio")` -> Fails
    * ...
    * `search(table, "token")` -> **Succeeds!** Returns token ID (e.g., "2005").
4.  The algorithm records the token "2005" and moves on to the rest of the word ("ization").
5.  It now repeats the process for "ization", but this time it prepends "##" to the keys, as this is a continuation of a word.
    * `search(table, "##ization")` -> Fails
    * `search(table, "##izatio")` -> Fails
    * ...
    * `search(table, "##ize")` -> **Succeeds!** Returns token ID (e.g., "2214").
6.  This continues until the entire word is consumed.

This greedy, iterative process involves many hash table lookups for a single word. The near-O(1) average lookup time provided by our Murmur3-powered hash table is what makes this algorithm computationally feasible and fast.

---

## 5. API Reference

| Function | Description |
| :--- | :--- |
| `HashTable* create_table(size_t size)` | Creates a hash table with a specified number of slots. |
| `void insert(HashTable *table, const char *key, const char *value)` | Inserts or updates a key-value pair in the table. |
| `char* search(HashTable *table, const char *key)` | Searches for a key and returns its value, or `NULL` if not found. Uses `simd_strcmp` for acceleration. |
| `void delete(HashTable *table, const char *key)` | Removes a key-value pair from the table. |
| `void free_table(HashTable *table)` | Frees all memory associated with the hash table, including all entries. |

