export function debounce<U extends unknown[]>(func: (...args: U) => unknown, timeout: number = 100): (...args: U) => void  {
  let timer: number;
  return (...args: U) => {
    clearTimeout(timer);
    timer = setTimeout(() => { func.apply(undefined, args); }, timeout);
  };
}
