# How CLI Tools Are Typically Installed

This documents common patterns for distributing and installing command-line tools.

## The `curl | bash` Pattern

Many popular tools use a one-liner install script:

```bash
# Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# nvm (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Deno
curl -fsSL https://deno.land/install.sh | sh

# Bun
curl -fsSL https://bun.sh/install | bash
```

### How It Works

1. **Download script** - `curl` fetches an install script from a URL
2. **Pipe to shell** - The script is piped directly to `bash` or `sh`
3. **Script does the work**:
   - Downloads the actual binary (platform-specific)
   - Places it in a standard location (`~/.local/bin`, `/usr/local/bin`, or tool-specific like `~/.deno/bin`)
   - Optionally updates shell config to add to PATH

### Common Install Script Actions

```bash
#!/bin/bash
set -e

# 1. Detect OS and architecture
OS=$(uname -s)
ARCH=$(uname -m)

# 2. Set install directory
INSTALL_DIR="${HOME}/.toolname/bin"
mkdir -p "$INSTALL_DIR"

# 3. Download the right binary
DOWNLOAD_URL="https://releases.example.com/toolname-${OS}-${ARCH}.tar.gz"
curl -fsSL "$DOWNLOAD_URL" | tar -xz -C "$INSTALL_DIR"

# 4. Make executable
chmod +x "$INSTALL_DIR/toolname"

# 5. Detect shell and update PATH
SHELL_CONFIG=""
if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/bin/bash" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
fi

# 6. Add to PATH if not already there
if [ -n "$SHELL_CONFIG" ]; then
    if ! grep -q "/.toolname/bin" "$SHELL_CONFIG"; then
        echo 'export PATH="$HOME/.toolname/bin:$PATH"' >> "$SHELL_CONFIG"
    fi
fi

# 7. Print success message with next steps
echo ""
echo "✓ toolname installed successfully!"
echo ""
echo "To get started, run:"
echo ""
echo "  source $SHELL_CONFIG"
echo ""
echo "Then you can use:"
echo ""
echo "  toolname --help"
echo ""
```

## Alternative: Homebrew Formula

For macOS users, distributing via Homebrew is common:

```bash
brew install toolname
```

This requires creating a Homebrew formula (Ruby file) and submitting to homebrew-core or hosting your own tap.

## Alternative: Package Managers

- **npm**: `npm install -g toolname`
- **pip**: `pip install toolname`
- **cargo**: `cargo install toolname`
- **go**: `go install github.com/user/toolname@latest`

## Best Practices for Install Scripts

1. **Use HTTPS** - Always download over secure connection
2. **Verify checksums** - Validate downloaded binaries
3. **Detect platform** - Support macOS (Darwin), Linux, and architectures (x86_64, arm64)
4. **Don't require sudo** - Install to user directories when possible
5. **Be idempotent** - Running twice shouldn't break anything
6. **Clear messaging** - Tell user what happened and next steps
7. **Respect existing config** - Don't duplicate PATH entries

## Example: What Memex Could Use

```bash
curl -fsSL https://memex.dev/install.sh | bash
```

The script would:
1. Download the memex binary for the user's platform
2. Install to `~/.memex/bin/`
3. Add to PATH in `.zshrc` or `.bashrc`
4. Print instructions to reload shell

User then runs:
```bash
source ~/.zshrc
memex doctor
```
