
# Bloggy - Selective Note Publishing System for SignalShore Blog

This is in terrible shape. I will update this later

This script scans your Notes directory for markdown files with 'public: true' in their YAML frontmatter,
and provides utilities for selective publishing and asset management for the SignalShore blog.

**Features**:
- List all public notes (with 'public: true' in frontmatter)
- Output all asset links referenced by public notes
- Create symlinks for public assets from Notes/assets to docs/posts/assets
- Create symlinks for notes tagged with #now to docs/now directory
- Extract forward (asset) links from a specific note

**Usage**:
    python bloggy.py [options]

**Options**:
    --list-public-posts      Output absolute paths of public notes (for piping to ln -s)
    --get-forward-links FILE Output forward (asset) links for a specific note file
    --list-public-assets     Output all assets referenced by public notes (whitelist)
    --link-public-assets     Create symlinks for public assets to docs/posts/assets
    --link-now-posts         Create symlinks for #now posts to docs/now directory
    -v, --verbose            Enable verbose logging output

**Example**:
    python bloggy.py --list-public-posts
    python bloggy.py --link-public-assets -v

Notes:
- The NOTES_DIR variable controls the location of your notes directory (default: ../Notes).
- Asset links are detected by searching for markdown links containing 'assets' in their path.
- #now posts are identified by the presence of 'now' in the 'tags' frontmatter field.
