import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MarkdownMessage } from '../components/MarkdownMessage';

describe('MarkdownMessage', () => {
  const markdown = [
    '# Heading 1',
    '',
    '```javascript',
    'console.log(42);',
    '```',
    '',
    'Inline math $E=mc^2$ and block math:',
    '',
    '$$',
    'a^2 + b^2 = c^2',
    '$$',
    '',
  ].join('\n');

  it('renders markdown elements', () => {
    const { container } = render(<MarkdownMessage content={markdown} />);
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading.textContent).toBe('Heading 1');
    expect(container.querySelector('pre code')?.textContent).toBe('console.log(42);');
    expect(container.querySelector('.katex')).not.toBeNull();
    expect(heading).toMatchSnapshot();
  });
});
