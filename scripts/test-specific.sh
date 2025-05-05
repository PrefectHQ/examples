#!/bin/bash
set -e

# Print environment info
echo "Environment:"
echo "Python: $(python --version 2>&1)"
echo "Running in: $(pwd)"

# Install dependencies if needed
if [[ "$1" == "--install" ]]; then
  echo "Installing dependencies..."
  # Check if uv is available, otherwise fall back to pip
  if command -v uv &> /dev/null; then
    echo "Using uv for package installation"
    # Try with uv first, but if it fails, fall back to pip
    if ! uv pip install -r internal/requirements.txt; then
      echo "uv installation failed, falling back to pip"
      # Directly use python -m pip to avoid issues with missing pip command
      python -m pip install --upgrade pip
      python -m pip install -r internal/requirements.txt
    fi
    
    # Same for Prefect
    if ! uv pip install "prefect>=2.0.0"; then
      echo "uv installation of prefect failed, falling back to pip"
      python -m pip install "prefect>=2.0.0"
    fi
  else
    echo "uv not found, using pip"
    python -m pip install --upgrade pip
    python -m pip install -r internal/requirements.txt
    python -m pip install "prefect>=2.0.0"
  fi
fi

# Specific files to test
CHANGED_FILES="01_getting_started/01_hello_world.py"
echo "Files to test: $CHANGED_FILES"

# Generate test plan
echo "Generating test plan..."
python -m internal.generate_test_plan --changed-files $CHANGED_FILES > test_plan.txt
cat test_plan.txt

# Run tests on examples
echo "Running tests..."
EXAMPLES=$(grep "^- " test_plan.txt | sed 's/^- //' || echo "")

if [ -z "$EXAMPLES" ]; then
  echo "No examples to test."
  exit 0
fi

echo "Running tests for the following examples:"
echo "$EXAMPLES"
echo "--------------------------------------"

# Create a temporary directory for modified examples
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

FAILED=0
for example in $EXAMPLES; do
  echo "Testing example: $example"
  
  # Create a temporary copy with frontmatter removed
  temp_file="$TEMP_DIR/$(basename "$example")"
  
  # Remove frontmatter (everything between the first two '---' lines)
  awk '
    BEGIN { in_frontmatter=0; frontmatter_end=0; }
    /^---$/ { 
      if (in_frontmatter == 0) { 
        in_frontmatter=1; 
        next; 
      } else if (frontmatter_end == 0) { 
        frontmatter_end=1; 
        next; 
      }
    }
    { if (in_frontmatter == 0 || frontmatter_end == 1) print $0; }
  ' "$example" > "$temp_file"
  
  # Run the modified example
  if python "$temp_file"; then
    echo "✅ Example $example passed."
  else
    echo "❌ Example $example failed."
    FAILED=$((FAILED+1))
  fi
  echo "--------------------------------------"
done

# Report summary
if [ $FAILED -gt 0 ]; then
  echo "❌ $FAILED examples failed."
  exit 1
else
  echo "✅ All examples passed."
fi 