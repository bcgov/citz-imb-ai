export interface ModalOption {
	text: string;
	onClick: () => void;
}

export interface ModalDialogProps {
	title: string;
	description: React.ReactNode;
	option1?: ModalOption;
	option2?: ModalOption;
	closeOnOutsideClick?: boolean;
}
