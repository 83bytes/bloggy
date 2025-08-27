#!/usr/bin/env python3
"""
Bloggy - Selective Note Publishing System for SignalShore Blog

This script scans your Notes directory for markdown files with 'public: true' in their YAML frontmatter,
and provides utilities for selective publishing and asset management for the SignalShore blog.

Features:
- List all public notes (with 'public: true' in frontmatter)
- Output all asset links referenced by public notes
- Create symlinks for public assets from Notes/assets to docs/posts/assets
- Create symlinks for notes tagged with #now to docs/now directory
- Extract forward (asset) links from a specific note

Usage:
    python bloggy.py [options]

Options:
    --list-public-posts      Output absolute paths of public notes (for piping to ln -s)
    --get-forward-links FILE Output forward (asset) links for a specific note file
    --list-public-assets     Output all assets referenced by public notes (whitelist)
    --link-public-assets     Create symlinks for public assets to docs/posts/assets
    --link-now-posts         Create symlinks for #now posts to docs/now directory
    -v, --verbose            Enable verbose logging output

Example:
    python bloggy.py --list-public-posts
    python bloggy.py --link-public-assets -v

Notes:
- The NOTES_DIR variable controls the location of your notes directory (default: ../Notes).
- Asset links are detected by searching for markdown links containing 'assets' in their path.
- #now posts are identified by the presence of 'now' in the 'tags' frontmatter field.

"""

import sys
import argparse
import re
import os
from pathlib import Path
from typing import List, Dict

NOTES_DIR = "../Notes"
# Regex pattern to extract link path from markdown links: [text](path)
LINK_REGEX = r"\[[^\]]*\]\(([^)]*)\)"


class NotesPublisher:
    def __init__(self, notes_dir: str = NOTES_DIR, verbose: bool = False):
        self.notes_dir = Path(notes_dir).resolve()
        self.verbose = verbose

    def log(self, message: str, force: bool = False):
        """Log message if verbose mode is enabled or force is True."""
        if self.verbose or force:
            print(message, file=sys.stderr)

    def parse_frontmatter(self, content: str) -> Dict[str, str]:
        """Parse YAML frontmatter from markdown content."""
        frontmatter = {}

        if not content.startswith("---"):
            return frontmatter

        # Find the end of frontmatter
        lines = content.splitlines()
        end_idx = None
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                end_idx = i
                break

        if end_idx is None:
            return frontmatter

        # Parse frontmatter lines
        for line in lines[1:end_idx]:
            if ":" in line:
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip()

        return frontmatter

    def is_public_note(self, file_path: Path) -> bool:
        """Check if a markdown file has 'public: true' in frontmatter."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            frontmatter = self.parse_frontmatter(content)
            return frontmatter.get("public", "").lower() == "true"

        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return False

    def has_now_tag(self, file_path: Path) -> bool:
        """Check if a markdown file contains the #now tag."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                frontmatter = self.parse_frontmatter(content)
            return "now" in frontmatter.get("tags", "").lower()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return False

    def find_public_notes(self) -> List[Path]:
        """Scan Notes directory for markdown files with public: true."""
        public_notes = []

        if not self.notes_dir.exists():
            print(f"Notes directory not found: {self.notes_dir}")
            return public_notes

        for md_file in self.notes_dir.rglob("*.md"):
            if self.is_public_note(md_file):
                public_notes.append(md_file)

        return public_notes

    def find_now_notes(self) -> List[Path]:
        """Scan Notes directory for markdown files with #now tag."""
        now_notes = []

        if not self.notes_dir.exists():
            print(f"Notes directory not found: {self.notes_dir}")
            return now_notes

        for md_file in self.notes_dir.rglob("*.md"):
            if self.has_now_tag(md_file):
                now_notes.append(md_file)

        return now_notes

    def scan_notes(self):
        """Scan and display public notes found."""
        self.log(f"Scanning for public notes in: {self.notes_dir}", force=True)
        public_notes = self.find_public_notes()

        self.log(f"\nFound {len(public_notes)} public notes:", force=True)
        for note in public_notes:
            self.log(f"  - {note}")

        return public_notes

    def output_public_paths(self):
        """Output absolute paths of public notes, one per line."""
        self.log("Finding public notes for path output...")
        public_notes = self.find_public_notes()

        self.log(f"Outputting {len(public_notes)} public note paths")
        for note in public_notes:
            print(note.resolve())

    def extract_assets_from_file(self, file_path: Path) -> List[str]:
        """Extract asset links from a single markdown file."""
        self.log(f"Extracting assets from: {file_path.name}")
        extracted_links = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                lines = content.splitlines()
                end_idx = 0
                frontmatter_separator_count = 0

                # Find end of frontmatter
                for i, line in enumerate(lines):
                    if line.strip() == "---":
                        frontmatter_separator_count += 1
                        if frontmatter_separator_count == 2:
                            end_idx = i
                            break

                # Extract links from content after frontmatter
                content_lines = lines[end_idx + 1 :] if end_idx > 0 else lines
                for line in content_lines:
                    # Find all link paths in the line
                    link_paths = re.findall(LINK_REGEX, line)
                    for link_path in link_paths:
                        # Only include links that contain 'assets' (as per LINK_PATTERN)
                        if "assets" in link_path:
                            self.log(f"  Found asset link: {link_path}")
                            extracted_links.append(link_path)

        except Exception as e:
            self.log(f"Error reading {file_path}: {e}", force=True)

        self.log(
            f"  Extracted {len(extracted_links)} asset links from {file_path.name}"
        )
        return extracted_links

    def output_forward_links(self, file_path: Path):
        """Extract forward links from note and print them."""
        self.log(f"Getting forward links from: {file_path}")
        extracted_links = self.extract_assets_from_file(file_path)

        self.log(f"Outputting {len(extracted_links)} forward links")
        for link_path in extracted_links:
            print(link_path)

    def collect_public_assets(self) -> List[str]:
        """Collect all asset links from public notes."""
        self.log("Starting collection of public assets...")
        public_notes = self.find_public_notes()
        all_public_assets = set()  # Use set to avoid duplicates

        self.log(
            f"Collecting assets from {len(public_notes)} public notes...", force=True
        )

        for note in public_notes:
            assets = self.extract_assets_from_file(note)
            all_public_assets.update(assets)
            self.log(f"  {note.name}: {len(assets)} assets", force=True)

        unique_assets = sorted(list(all_public_assets))
        self.log(f"Total unique public assets found: {len(unique_assets)}")
        return unique_assets

    def output_public_assets(self):
        """Output all assets used by public notes (whitelist)."""
        self.log("Starting public assets output...")
        public_assets = self.collect_public_assets()

        self.log(
            f"Found {len(public_assets)} unique assets in public notes:", force=True
        )

        for asset_path in public_assets:
            print(asset_path)

    def link_public_assets(self, target_dir: Path | None = None):
        """Create symlinks for public assets from Notes/assets to docs/posts/assets."""
        self.log("Starting public assets linking process...")

        if target_dir is None:
            target_dir = Path("docs/posts/assets")

        self.log(f"Target directory: {target_dir}")
        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)
        self.log("Target directory created/verified")

        # Get the source assets directory
        source_assets_dir = self.notes_dir / "assets"
        self.log(f"Source assets directory: {source_assets_dir}")

        if not source_assets_dir.exists():
            self.log(
                f"Source assets directory not found: {source_assets_dir}", force=True
            )
            return

        # Collect public assets
        public_assets = self.collect_public_assets()

        self.log(
            f"Linking {len(public_assets)} public assets to {target_dir}...", force=True
        )

        linked_count = 0
        for asset_path in public_assets:
            # Convert relative asset path to absolute source path
            source_path = source_assets_dir / asset_path.replace("assets/", "")
            target_path = target_dir / asset_path.replace("assets/", "")

            self.log(f"  Source: {source_path}")
            self.log(f"  Target: {target_path}")

            # Create parent directories in target if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Remove existing symlink if it exists
            if target_path.exists() or target_path.is_symlink():
                target_path.unlink()

            # Create symlink
            if source_path.exists():
                os.symlink(source_path.resolve(), target_path)
                linked_count += 1
            else:
                self.log(f"Warning: Source file not found: {source_path}", force=True)

        self.log(
            f"Successfully linked {linked_count}/{len(public_assets)} assets",
            force=True,
        )

    def link_now_posts(self, target_dir: Path | None = None):
        """Create symlinks for #now posts to docs/now directory."""
        self.log("Starting #now posts linking process...")

        if target_dir is None:
            target_dir = Path("docs/now")

        self.log(f"Target directory: {target_dir}")
        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)
        self.log("Target directory created/verified")

        # Find all #now posts
        now_posts = self.find_now_notes()
        self.log(f"Found {len(now_posts)} #now posts", force=True)

        linked_count = 0
        for post in now_posts:
            filename = post.name

            # Check if filename already has date format (yyyy-mm-dd)
            if (
                filename.startswith(("20", "19"))
                and len(filename) >= 10
                and filename[4] == "-"
                and filename[7] == "-"
            ):
                # File already has date format, use as-is
                target_filename = filename
                self.log(f"File {filename} already has date format, linking directly")
            else:
                # Extract date from frontmatter
                try:
                    with open(post, "r", encoding="utf-8") as f:
                        content = f.read()
                    frontmatter = self.parse_frontmatter(content)
                    date_str = frontmatter.get("date", "")

                    if date_str:
                        target_filename = f"{date_str}_{filename}"
                    else:
                        target_filename = filename
                except Exception as e:
                    self.log(f"Error reading frontmatter from {post}: {e}", force=True)
                    target_filename = filename

            target_path = target_dir / target_filename
            self.log(f"  Source: {post}")
            self.log(f"  Target: {target_path}")

            # Remove existing symlink if it exists
            if target_path.exists() or target_path.is_symlink():
                target_path.unlink()

            # Create symlink
            os.symlink(post.resolve(), target_path)
            linked_count += 1
            self.log(f"  Linked: {target_filename}", force=True)

        self.log(
            f"Successfully linked {linked_count} #now posts to {target_dir}",
            force=True,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Selective note publishing for SignalShore blog"
    )
    parser.add_argument(
        "--list-public-posts",
        action="store_true",
        help="Output paths of public notes for piping to ln -s",
    )
    # output the forward links
    parser.add_argument(
        "--get-forward-links",
        help="Output forward links for a specific note file",
        type=Path,
    )
    parser.add_argument(
        "--list-public-assets",
        action="store_true",
        help="Output all assets referenced by public notes (whitelist)",
    )
    parser.add_argument(
        "--link-public-assets",
        action="store_true",
        help="Create symlinks for public assets from Notes/assets to docs/posts/assets",
    )
    parser.add_argument(
        "--link-now-posts",
        action="store_true",
        help="Create symlinks for #now posts to docs/now directory",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging output",
    )

    args = parser.parse_args()

    publisher = NotesPublisher(verbose=args.verbose)

    if args.list_public_posts:
        publisher.output_public_paths()
    elif args.get_forward_links:
        publisher.output_forward_links(args.get_forward_links)
    elif args.list_public_assets:
        publisher.output_public_assets()
    elif args.link_public_assets:
        publisher.link_public_assets()
    elif args.link_now_posts:
        publisher.link_now_posts()
    else:
        publisher.scan_notes()


if __name__ == "__main__":
    main()
