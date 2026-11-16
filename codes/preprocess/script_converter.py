from bs4 import BeautifulSoup
import re
import os
from difflib import SequenceMatcher

class SubScriptConverter:
    """
    Advanced converter for changing A HTML .sub. notation to B HTML <sub> tags
    Combines tag content matching with context similarity comparison
    """

    def __init__(self, context_window=50, similarity_threshold=0.5, **kwargs):
        """
        Initialize converter

        Args:
            context_window (int): Size of context window around tags/patterns
            similarity_threshold (float): Minimum similarity to consider a match
            **kwargs: Additional options (verbose)
        """
        self.context_window = context_window
        self.similarity_threshold = similarity_threshold
        self.verbose = kwargs.get('verbose', True)
        self.exclude_words = kwargs.get('exclude_words', [])

    def extract_tags_from_b(self, html, tag_type='sub'):
        """
        Extract all tags of specified type from HTML B with context

        Args:
            html (str): HTML content
            tag_type (str): Tag type ('sub' or 'sup')

        Returns:
            list: List of tag information
        """
        soup = BeautifulSoup(html, 'html.parser')
        tags = soup.find_all(tag_type)
        results = []

        print(f"[B HTML] Extracting <{tag_type}> tags")


        for tag_index, tag in enumerate(tags):
            # Get tag content
            tag_content = tag.get_text().strip()

            # Get parent element and its text
            parent = tag.parent
            parent_html = str(parent)
            tag_html = str(tag).strip()

            # Try to find tag content position in parent text
            tag_pos = parent_html.find(tag_html)

            before_html = parent_html[:tag_pos]
            after_html = parent_html[tag_pos + len(tag_html):]

            # Convert to plain text
            before_soup = BeautifulSoup(before_html, 'html.parser')
            after_soup = BeautifulSoup(after_html, 'html.parser')

            before_text = before_soup.get_text()[-self.context_window:]
            after_text = after_soup.get_text()[:self.context_window]
            if ' ' in tag.get_text():
                if tag.get_text().index(' '):
                    after_text = ' ' + after_text
                else:
                    before_text = before_text + ' '

            # Get parent text for context comparison
            parent_text = parent.get_text()

            # Store tag information
            tag_info = {
                'tag': tag,
                'content': tag_content,
                'parent': parent,
                'parent_text': parent_text,
                'before_text': before_text,
                'after_text': after_text,
                'full_context': before_text + tag_content + after_text
            }
            results.append(tag_info)

            #print(f"Found <{tag_type}> tag {tag_index+1}: {tag_html}")
            #print(f"  Content: {tag_content}")
            #print(f"  Context: ...{before_text[-30:]}[{tag_content}]{after_text[:30]}...")

        #print(f"Total <{tag_type}> tags found in B HTML: {len(results)}")
        return results


    def remove_words_from_text(self, text):
        """
        Remove specified words from text

        Args:
            text (str): Text to process

        Returns:
            str: Text with specified words removed
        """

        # Replace matched words with empty string
        text = re.sub(r'\.sub\.', '', text)
        text = re.sub(r'\.sup\.', '', text)
        text = re.sub('<br>', '', text)
        text = re.sub('<br/>', '', text)
        text = re.sub(r'\s+', ' ', text)

        return text


    def find_matching_patterns_in_a(self, a_html, tag_infos, pattern_type='sub'):
        """
        Find patterns in HTML A that match tag contents from HTML B
        Uses both content matching and context similarity

        Args:
            a_html (str): HTML A content
            tag_infos (list): Tag information from HTML B
            pattern_type (str): Pattern type ('sub' or 'sup')

        Returns:
            list: List of conversion mappings
        """
        conversions = []

        #print(f"\n[A HTML] Finding .{pattern_type}. patterns matching B HTML tags")

        for tag_idx, tag_info in enumerate(tag_infos):
            tag_content = tag_info['content']
            tag = tag_info['tag']
            tag_context = tag_info['full_context']

            # Create pattern to find in A HTML
            # Look for any word followed by .sub. and the exact tag content
            pattern = r'\.{}\.({})'.format(pattern_type, re.escape(tag_content))

            # Find all matches
            matches = list(re.finditer(pattern, a_html))

            if matches:
                # If multiple matches, use context similarity to find the best one
                best_match = None
                highest_similarity = self.similarity_threshold

                for match in matches:
                    full_pattern = match.group(0)
                    start_pos = match.start()
                    end_pos = match.end()

                    # Extract context around pattern
                    context_start = max(0, start_pos - self.context_window)
                    context_end = min(len(a_html), end_pos + self.context_window)
                    pattern_context = a_html[context_start:context_end]
                    processed_pattern_context = self.remove_words_from_text(pattern_context)

                    # Calculate context similarity
                    similarity = SequenceMatcher(None, processed_pattern_context, tag_context).ratio()

                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        best_match = {
                            'match': match,
                            'similarity': similarity,
                            'context': processed_pattern_context
                        }

                if best_match:
                    match = best_match['match']
                    full_pattern = match.group(0)
                    content = match.group(1)
                    start_pos = match.start()

                    # Create replacement
                    replacement = f"<{pattern_type}>{content}</{pattern_type}>"

                    # Store conversion
                    conversion = {
                        'original': full_pattern,
                        'replacement': replacement,
                        'position': start_pos,
                        'similarity': best_match['similarity'],
                        'tag_info': tag_info
                    }

                    conversions.append(conversion)

                    #print(f"Best match for tag {tag_idx+1}:")
                    #print(f"  Original: {best_match['context']}")
                    #print(f"  Replacement: {tag_context}")
                    #print(f"  Similarity: {best_match['similarity']:.4f}")
            else:
                print(f"No matching pattern found for tag {tag_idx+1}: <{tag.name}>{tag_content}</{tag.name}>")

        #print(f"Total matching patterns found: {len(conversions)}")
        return conversions

    def apply_conversions(self, a_html, conversions):
        """
        Apply all conversions to HTML A

        Args:
            a_html (str): Original HTML A content
            conversions (list): List of conversion mappings

        Returns:
            str: Converted HTML
        """
        # Sort conversions by position in reverse order to prevent position shifts
        conversions = sorted(conversions, key=lambda x: x['position'], reverse=True)

        # Create a copy of the original HTML
        converted_html = a_html

        #print("\n[CONVERSION] Applying conversions")

        for idx, conversion in enumerate(conversions):
            original = conversion['original']
            replacement = conversion['replacement']
            similarity = conversion.get('similarity', 0)

            #print(f"Applying conversion {idx+1}:")
            #print(f"  {original} → {replacement}")
            #print(f"  Context similarity: {similarity:.4f}")

            # Perform replacement
            converted_html = converted_html.replace(original, replacement)

        #print(f"All {len(conversions)} conversions applied")
        return converted_html

    def convert_document(self, a_html, b_html):
        """
        Convert HTML A to match tag structure in HTML B

        Args:
            a_html (str): HTML A content (with .sub. notation)
            b_html (str): HTML B content (with <sub> tags)

        Returns:
            str: Converted HTML
        """
        #print("[STARTING CONVERSION PROCESS]")
        #print("=" * 50)

        # Extract tags from HTML B
        b_sub_tags = self.extract_tags_from_b(b_html, 'sub')
        b_sup_tags = self.extract_tags_from_b(b_html, 'sup')

        # Find matching patterns in HTML A
        sub_conversions = self.find_matching_patterns_in_a(a_html, b_sub_tags, 'sub')
        sup_conversions = self.find_matching_patterns_in_a(a_html, b_sup_tags, 'sup')

        # Apply all conversions
        all_conversions = sub_conversions + sup_conversions
        converted_html = self.apply_conversions(a_html, all_conversions)


        #print("\n[CONVERSION COMPLETE]")
        #print(f"Total conversions: {len(all_conversions)}")
        #print("=" * 50)

        return converted_html

    def process_files(self, patent_id, input_dir='input/clean_html', output_file_path=None):
        """Load a prepared local HTML file without a live web dependency.

        The research pipeline compared a locally cleaned document with a live
        Google Patents page to repair subscript and superscript notation.  A
        public reproduction must not change when that page changes, so the
        release input contract requires those tags to be repaired beforehand.
        This method retains only deterministic character normalization.
        """
        input_path = os.path.join(input_dir, f"{patent_id}.html")
        with open(input_path, 'r', encoding='utf-8') as file:
            converted_html = file.read()

        replacements = (
            (r'\.times\.', '×'),
            (r'\.degree\.', '°'),
            ('−', '-'),
            ('—', '-'),
            ('\u2003', ' '),
            ('\u2009', ' '),
            (r'\? C\.', '&deg;C'),
            (r'\?10\.sup\.', '&times;10.sup.'),
            (r'\.sup\.\?', '.sup.-'),
            (r'\?g/', '&micro;g/'),
        )
        for pattern, replacement in replacements:
            converted_html = re.sub(pattern, replacement, converted_html)

        if output_file_path:
            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.write(converted_html)

        return converted_html
