import { useEffect, useState } from "react";

import type { ScrollButtonProps } from "@/types";
import { CaretDown, CaretUp } from "@phosphor-icons/react";

import "./ScrollButton.scss";

// ScrollButton component
const ScrollButton: React.FC<ScrollButtonProps> = ({
	scrollableElementId,
	generationComplete,
}) => {
	// State to track if the user is at the bottom of the scrollable area
	const [atBottom, setAtBottom] = useState(false);

	// Function to handle scroll events
	const handleScroll = () => {
		const element = document.getElementById(scrollableElementId);
		if (element) {
			const isBottom =
				element.scrollHeight - element.scrollTop - element.clientHeight < 1;
			setAtBottom(isBottom);
		}
	};

	// Function to scroll to top or bottom
	const scrollTo = () => {
		const element = document.getElementById(scrollableElementId);
		if (element) {
			element.scrollTo({
				top: atBottom ? 0 : element.scrollHeight,
				behavior: generationComplete ? "smooth" : "auto",
			});
		}
	};

	// Effect to add and remove scroll event listener
	useEffect(() => {
		const element = document.getElementById(scrollableElementId);
		if (element) {
			element.addEventListener("scroll", handleScroll);
		}

		return () => {
			if (element) {
				element.removeEventListener("scroll", handleScroll);
			}
		};
	}, [scrollableElementId]);

	// Render the scroll button
	return (
		<div className="scroll-button-container">
			<button
				className="scroll-button scroll-button-icon"
				onClick={scrollTo}
				title={atBottom ? "Scroll to Top" : "Scroll to Bottom"}
			>
				{atBottom ? <CaretUp size={20} /> : <CaretDown size={20} />}
			</button>
		</div>
	);
};

export default ScrollButton;
