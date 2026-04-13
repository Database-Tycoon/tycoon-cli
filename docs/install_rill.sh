#!/bin/sh
set -e

# Install dependencies
apt-get update && apt-get install -y curl unzip git

# Pre-emptively add to PATH
echo 'export PATH=$HOME/.rill:$PATH # Added by Rill install' >> /root/.bashrc

# Run the Rill installation, ignoring errors from tput
export TERM=dumb
curl -s https://rill.sh | sh -s -- --non-interactive "$HOME/.rill" || true

# Add rill to the path for the current session
export PATH="$HOME/.rill:$PATH"

# Verify installation
/root/.rill/rill version
