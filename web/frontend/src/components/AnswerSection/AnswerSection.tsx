import type React from "react";
import { useCallback, useContext, useEffect, useRef, useState } from "react";

import { assets } from "@/assets/icons/assets";
import SourcesSection from "@/components/AnswerSection/SourcesSection/SourcesSection";
import ImagesSection from "@/components/AnswerSection/ImagesSection/ImagesSection";
import FeedbackBar from "@/components/FeedbackBar/FeedbackBar";
import ModalDialog from "@/components/Modal/ModalDialog";
import { Context } from "@/context/Context";
import type { AnswerSectionProps, ImageItem, TopKItem } from "@/types";
import {
	addChatInteraction,
	initAnalytics,
	trackLLMResponseInteraction,
	trackSourceClick,
} from "@/utils/analyticsUtil";
import { getUserId } from "@/utils/authUtil";
import { debounce } from "@/utils/debounceUtil";
import { CaretDown } from "@phosphor-icons/react";

import "./AnswerSection.scss";

// Component for displaying AI-generated answers and related sources
const AnswerSection: React.FC<AnswerSectionProps> = ({
	message,
	isLastMessage,
	generationComplete,
	recording_id,
}) => {
	const context = useContext(Context);
	const [selectedItem, setSelectedItem] = useState<TopKItem | null>(null);
	const [isAnswerComplete, setIsAnswerComplete] = useState(false);
	const [showSources, setShowSources] = useState(true);
	const [hoverStartTime, setHoverStartTime] = useState<number | null>(null);
	const [chatIndex, setChatIndex] = useState<number | null>(null);
	const analyticsInitialized = useRef(false);

	// Ensure the component is used within a ContextProvider
	if (!context) {
		throw new Error("AnswerSection must be used within a ContextProvider");
	}

	// Get user ID and messages from context
	const userId = getUserId();
	const { messages } = context;

	// Create a debounced version of the hover tracking function
	const debouncedTrackHover = useRef(
		debounce((...args: [number, number]) => {
			const [chatIndex, duration] = args;
			trackLLMResponseInteraction(chatIndex, "hover", duration);
		}, 1000),
	).current;

	// Initialize analytics on component mount
	useEffect(() => {
		if (!analyticsInitialized.current) {
			initAnalytics(userId);
			analyticsInitialized.current = true;
		}
	}, [userId]);

	// Record chat interaction when generation is complete
	useEffect(() => {
		if (generationComplete && isLastMessage) {
			const aiMessages = messages.filter((msg) => msg.type === "ai");
			if (aiMessages.length > 0) {
				const lastAiMessage = aiMessages[aiMessages.length - 1];
				const newChatIndex = addChatInteraction(
					recording_id,
					lastAiMessage.topk,
					generationComplete,
				);
				setChatIndex(newChatIndex);
			}
		}
	}, [generationComplete, isLastMessage, messages, recording_id]);

	// Show answer complete animation after a delay
	useEffect(() => {
		if (generationComplete) {
			const timer = setTimeout(() => setIsAnswerComplete(true), 500);

			return () => clearTimeout(timer);
		}

		return () => {};
	}, [generationComplete]);

	// Event handlers
	const handleCardClick = useCallback(
		(item: TopKItem, index: number) => {
			setSelectedItem(item);
			if (chatIndex !== null) {
				trackSourceClick(chatIndex, index);
			}
		},
		[chatIndex],
	);

	// Handler for image clicks
	const handleImageClick = useCallback(
		(_image: ImageItem, index: number) => {
			// Only track analytics, don't show the source modal
			if (chatIndex !== null) {
				trackSourceClick(chatIndex, index);
			}
		},
		[chatIndex],
	);

	// Handles hover tracking for the LLM response
	const handleLLMResponseHover = useCallback(
		(isHovering: boolean) => {
			if (chatIndex === null) return;

			if (isHovering) {
				setHoverStartTime(Date.now());
			} else if (hoverStartTime !== null) {
				const hoverDuration = Date.now() - hoverStartTime;
				debouncedTrackHover(chatIndex, hoverDuration);
				setHoverStartTime(null);
			}
		},
		[chatIndex, hoverStartTime, debouncedTrackHover],
	);

	// Handles click tracking for the LLM response
	const handleLLMResponseClick = useCallback(() => {
		if (chatIndex !== null) {
			trackLLMResponseInteraction(chatIndex, "click");
		}
	}, [chatIndex]);

	// Handles closing the modal
	const handleCloseModal = useCallback(() => {
		setSelectedItem(null);
	}, []);

	// Formats the description for the modal
	const formatDescription = useCallback(
		(item: TopKItem) => (
			<div>
				<p>
					<strong>Score:</strong> {item.score || "N/A"}
				</p>
				<p>
					<strong>Act ID:</strong> {item.ActId || "N/A"}
				</p>
				<p>
					<strong>Section Name:</strong> {item.sectionName || "N/A"}
				</p>
				<p>
					<strong>Section ID:</strong> {item.sectionId || "N/A"}
				</p>
				<p>
					<strong>Regulations:</strong> {item.Regulations || "N/A"}
				</p>
				<p>
					<strong>URL:</strong>{" "}
					{item.url ? (
						<a href={item.url} target="_blank" rel="noopener noreferrer">
							{item.url}
						</a>
					) : (
						"N/A"
					)}
				</p>
				<p>
					<strong>Text:</strong> {item.text || "N/A"}
				</p>
				<p>
					{item.references &&
						item.references.length > 0 &&
						item.references[0].refActId && (
							<div>
								<strong>References:</strong>
								{item.references.map((ref, index) => (
									<ul key={`ref-${index}`}>
										<li key={`act-${index}`}>
											{ref.refActId ? "Act Name: " + ref.refActId : ""}
										</li>
										<li key={`section-${index}`}>
											{ref.refSectionId
												? "Section Id: " + ref.refSectionId
												: ""}
										</li>
										<li key={`text-${index}`}>
											{ref.refText ? "Text: " + ref.refText : ""}
										</li>
										<hr></hr>
									</ul>
								))}
							</div>
						)}
				</p>
			</div>
		),
		[],
	);

	// Truncates text to a maximum length
	const truncateText = useCallback((text: string, maxLength: number) => {
		return text.length <= maxLength ? text : `${text.slice(0, maxLength)}...`;
	}, []);

	// Prepare image data for ImagesSection
	const prepareImageData = useCallback((): ImageItem[] => {
		if (!message.topk || message.topk.length === 0) {
			return [];
		}

		// Filter topk items that have image data and create ImageItem objects
		return message.topk
			.filter((item) => item.ImageUrl && item.file_name) // Only include items with image data
			.map((item) => {
				const baseItem: ImageItem = {
					url: item.ImageUrl,
					alt: item.file_name,
					filename: item.file_name,
				};

				// Include topkItem for analytics tracking
				baseItem.topkItem = item;

				return baseItem;
			});
	}, [message.topk]);

	return (
		<div className="answer-section">
			{/* AI response */}
			<div
				className="message-title"
				onMouseEnter={() => handleLLMResponseHover(true)}
				onMouseLeave={() => handleLLMResponseHover(false)}
				onClick={handleLLMResponseClick}
			>
				<img src={assets.bc_icon} alt="BC AI" />
				<p dangerouslySetInnerHTML={{ __html: message.content }}></p>
			</div>

			{/* Sources section */}
			{message.topk && message.topk.length > 0 && (
				<div className={`sources-section ${isAnswerComplete ? "fade-in" : ""}`}>
					<h3
						onClick={() => setShowSources(!showSources)}
						style={{ cursor: "pointer" }}
					>
						Sources
						<CaretDown
							size={24}
							className={`chevron-icon ${showSources ? "" : "rotated"}`}
						/>
					</h3>
					<SourcesSection
						showSources={showSources}
						message={message}
						handleCardClick={handleCardClick}
						truncateText={truncateText}
					/>
					{/* Only show ImagesSection if there are images to display */}
					{prepareImageData().length > 0 && (
						<ImagesSection
							showSources={showSources}
							images={prepareImageData()}
							onImageClick={handleImageClick}
						/>
					)}
				</div>
			)}

			{/* Feedback bar */}
			{isLastMessage && generationComplete && <FeedbackBar />}

			{/* Modal for displaying source details */}
			{selectedItem && (
				<ModalDialog
					title={selectedItem.ActId || "Details"}
					description={formatDescription(selectedItem)}
					option1={{
						text: "Close",
						onClick: handleCloseModal,
					}}
					closeOnOutsideClick={true}
				/>
			)}
		</div>
	);
};

export default AnswerSection;
