"""KnowledgeBase — Loads company-specific knowledge base files."""
import os
import glob
from core.logger import get_logger

logger = get_logger(__name__)


class KnowledgeBase:
    """Reads and manages knowledge base files for a company."""

    def __init__(self, path="knowledge_base"):
        self.path = path

    def load(self, file_filter=None):
        """
        Reads files from company-specific knowledge_base folder.

        Args:
            file_filter: Optional list of substrings to filter files.
                         If None, loads all TRI_* and *premium* files.
                         Example: ["essencia", "voz"] loads TRI_ESSENCIA.txt and TRI_VOZ.txt

        Returns empty string if no knowledge base exists.
        """
        kb_content = ""
        try:
            if not os.path.exists(self.path):
                logger.info("No knowledge base found at '%s'. Using AI's general knowledge.", self.path)
                return ""

            files = glob.glob(f"{self.path}/*.txt")
            if not files:
                logger.info("No .txt files in '%s'. Using AI's general knowledge.", self.path)
                return ""

            if file_filter is None:
                file_filter = ["tri_essencia", "tri_voz", "premium"]

            loaded_count = 0
            for file_path in files:
                filename = os.path.basename(file_path).lower()

                should_load = any(pattern in filename for pattern in file_filter)

                if should_load:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        kb_content += f"\n--- ARQUIVO: {os.path.basename(file_path)} ---\n{content}\n"
                        loaded_count += 1
                        logger.info("Loaded KB: %s (%s chars)", os.path.basename(file_path), f"{len(content):,}")
                else:
                    logger.debug("Skipped KB file: %s (not in filter)", os.path.basename(file_path))

            if not kb_content:
                logger.warning("No matching KB files found for filter %s.", file_filter)
            else:
                logger.info("Loaded %d KB file(s) (%s total chars)", loaded_count, f"{len(kb_content):,}")

            return kb_content
        except Exception as e:
            logger.error("Could not load knowledge base: %s", e)
            return ""

    def load_voice_guide(self):
        """
        Loads just the TRI_VOZ.txt file for the Humanizer agent.
        Returns the voice guide content or empty string.
        """
        try:
            voz_files = glob.glob(f"{self.path}/*VOZ*.txt") + glob.glob(f"{self.path}/*voz*.txt")

            if voz_files:
                with open(voz_files[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.info("Voice Guide loaded: %s (%s chars)", os.path.basename(voz_files[0]), f"{len(content):,}")
                    return content

            logger.warning("No TRI_VOZ file found. Humanizer will use default voice settings.")
            return ""
        except Exception as e:
            logger.error("Could not load voice guide: %s", e)
            return ""
