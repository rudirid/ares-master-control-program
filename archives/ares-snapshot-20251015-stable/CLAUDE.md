- Load ares.  Ares builds the foundation for all future subagents
# Create standardized directory structure

mkdir -p ~/.claude/subagents
mkdir -p ~/.claude/subagents/archive
mkdir -p ~/.claude/subagents/templates

# Create subagent management system
# Build a script that can:
# - List all available subagents
# - Test subagents for errors
# - Version subagents
# - Deploy/rollback subagents