/* eslint-disable @typescript-eslint/no-unused-vars */
"use client";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const markdownComponents: Record<string, React.FC<any>> = {
  p: ({ node, ...props }) => <p className="text-base leading-8 mb-4" {...props} />,
  a: ({ node, ...props }) => (
    <a className="text-indigo-600 hover:underline wrap-break-word" {...props} />
  ),
  h1: ({ node, ...props }) => <h1 className="text-3xl font-semibold mt-8 mb-4" {...props} />,
  h2: ({ node, ...props }) => <h2 className="text-2xl font-semibold mt-7 mb-4" {...props} />,
  h3: ({ node, ...props }) => <h3 className="text-xl font-semibold mt-6 mb-3" {...props} />,
  h4: ({ node, ...props }) => <h4 className="text-lg font-medium mt-5 mb-2" {...props} />,
  ul: ({ node, ...props }) => <ul className="list-disc pl-8 space-y-3 mb-4" {...props} />,
  ol: ({ node, ...props }) => <ol className="list-decimal pl-8 space-y-3 mb-4" {...props} />,
  li: ({ node, ...props }) => <li className="mb-2" {...props} />,
  blockquote: ({ node, ...props }) => (
    <blockquote
      className="border-l-4 pl-6 italic text-muted-foreground bg-muted p-4 rounded-md my-4"
      {...props}
    />
  ),
  img: ({ node, ...props }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img className="max-w-full rounded-md my-4" alt={props.alt} {...props} />
  ),
  table: ({ node, ...props }) => (
    <div className="overflow-auto my-4">
      <table className="min-w-full text-sm" {...props} />
    </div>
  ),
  thead: ({ node, ...props }) => <thead className="bg-muted text-sm" {...props} />,
  th: ({ node, ...props }) => <th className="px-4 py-3 text-left font-medium" {...props} />,
  td: ({ node, ...props }) => <td className="px-4 py-3 align-top" {...props} />,
  tr: ({ node, ...props }) => <tr className="border-b" {...props} />,
};

export default markdownComponents;
