"use client";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const markdownComponents: Record<string, React.FC<any>> = {
  p: ({ ...props }) => <p className="text-base leading-8 mb-4" {...props} />,
  a: ({ ...props }) => <a className="text-indigo-600 hover:underline wrap-break-word" {...props} />,
  h1: ({ ...props }) => <h1 className="text-3xl font-semibold mt-8 mb-4" {...props} />,
  h2: ({ ...props }) => <h2 className="text-2xl font-semibold mt-7 mb-4" {...props} />,
  h3: ({ ...props }) => <h3 className="text-xl font-semibold mt-6 mb-3" {...props} />,
  h4: ({ ...props }) => <h4 className="text-lg font-medium mt-5 mb-2" {...props} />,
  ul: ({ ...props }) => <ul className="list-disc pl-8 space-y-3 mb-4" {...props} />,
  ol: ({ ...props }) => <ol className="list-decimal pl-8 space-y-3 mb-4" {...props} />,
  li: ({ ...props }) => <li className="mb-2" {...props} />,
  blockquote: ({ ...props }) => (
    <blockquote
      className="border-l-4 pl-6 italic text-muted-foreground bg-muted p-4 rounded-md my-4"
      {...props}
    />
  ),
  img: ({ ...props }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img className="max-w-full rounded-md my-4" alt={props.alt} {...props} />
  ),
  table: ({ ...props }) => (
    <div className="overflow-auto my-4">
      <table className="min-w-full text-sm" {...props} />
    </div>
  ),
  thead: ({ ...props }) => <thead className="bg-muted text-sm" {...props} />,
  th: ({ ...props }) => <th className="px-4 py-3 text-left font-medium" {...props} />,
  td: ({ ...props }) => <td className="px-4 py-3 align-top" {...props} />,
  tr: ({ ...props }) => <tr className="border-b" {...props} />,
  code: ({ inline, className, children, ...props }) => {
    if (inline) {
      return (
        <code className="bg-muted px-2 py-0.5 rounded text-sm font-mono" {...props}>
          {children}
        </code>
      );
    }

    return (
      <pre className="bg-surface p-4 rounded-md overflow-auto my-4">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    );
  },
};

export default markdownComponents;
