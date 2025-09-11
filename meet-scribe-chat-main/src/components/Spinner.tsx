// File: src/components/Spinner.tsx

export const Spinner = () => {
  return (
    <div className="flex justify-center items-center py-12">
      <div
        className="w-12 h-12 rounded-full animate-spin border-4 border-solid border-primary border-t-transparent"
        role="status"
        aria-label="loading"
      ></div>
    </div>
  );
};