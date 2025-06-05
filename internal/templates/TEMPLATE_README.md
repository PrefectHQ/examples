# Prefect Article Templates

This directory contains templates for creating opinionated articles about Prefect features.

## Available Templates

1. **template.py** - Use this when writing a Python file that will be converted to MDX

## Template Structure

These templates follow a consistent structure for Prefect feature articles:

1. **Title and Introduction** - Brief overview of the feature with emoji
2. **Key Capabilities** - Bulleted list of parameters/options with explanations
3. **Use Cases** - When and why to use this feature
4. **Comparisons** - How this feature relates to alternatives or similar features
5. **Running Examples** - How to run the example code
6. **Code Organization** - Overview of the code structure
7. **Code Examples** - Multiple sections with code snippets and explanations
8. **What Just Happened?** - Step-by-step explanation of code execution
9. **Benefits** - Summary of advantages the feature provides
10. **Why This Is Important** - Broader significance in real-world data engineering
11. **Conclusion** - Value proposition of the feature

## When Writing Content

- **Be opinionated**: These are not just technical documentation but guidance on how to use Prefect effectively
- **Include real-world scenarios**: Help users understand when and why to use features
- **Provide best practices**: Offer clear recommendations based on experience
- **Use emojis sparingly**: They add personality but don't overdo it
- **Include code examples**: Always demonstrate concepts with runnable code
- **Explain "why"**: Don't just describe what a feature does, but why it matters

## Python File Format

When writing Python files that will be converted to MDX:
- Add YAML frontmatter between triple-dashes at the top
- Use comments with `#` for all descriptive text
- Use `# ##` for section headings
- Use `# *` for bullet points
- Code will be preserved as-is in the final MDX

## Converting Python to MDX

The Python files are automatically converted to MDX using the `internal/generate_docs.py` script. Run:

```bash
python -m internal.generate_docs -o docs
```

This will process all Python files and generate corresponding MDX files in the docs directory. 