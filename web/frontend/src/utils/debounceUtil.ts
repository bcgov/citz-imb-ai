//Creates a debounced function that delays invoking `func` until after `wait` millisecond have elapsed since the last time the debounced function was invoked.

export const debounce = <T extends (...args: number[]) => void>(
	func: T,
	wait: number,
): ((...args: Parameters<T>) => void) => {
	let timeout: ReturnType<typeof setTimeout> | null = null;

	return (...args: Parameters<T>) => {
		if (timeout !== null) {
			clearTimeout(timeout);
		}
		timeout = setTimeout(() => func(...args), wait);
	};
};
