import {useState} from "react";

/**
 * Custom hook for persisting state in localStorage
 */
export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
    // Get stored value or use initial value
    const [storedValue, setStoredValue] = useState<T>(() => {
        if (typeof window === "undefined") {
            return initialValue;
        }
        try {
            const item = window.localStorage.getItem(key);
            return item ? JSON.parse(item) : initialValue;
        } catch (error) {
            console.error(`Error loading localStorage key "${key}":`, error);
            return initialValue;
        }
    });

    // Update localStorage when value changes
    const setValue = (value: T) => {
        try {
            setStoredValue(value);
            if (typeof window !== "undefined") {
                window.localStorage.setItem(key, JSON.stringify(value));
            }
        } catch (error) {
            console.error(`Error saving localStorage key "${key}":`, error);
        }
    };

    return [storedValue, setValue];
}
