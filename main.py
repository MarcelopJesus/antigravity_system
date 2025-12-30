import json
import os
import time
from core.gemini_brain import GeminiBrain
from core.sheets_client import SheetsClient
from core.wordpress_client import WordPressClient

def main():
    print("🚀 SEO Orchestrator Starting...")
    
    # Check for service account
    if not os.path.exists('config/service_account.json'):
         print("❌ Error: 'config/service_account.json' missing. accessing Google Sheets will fail.")
         print("Please download it from Google Cloud Console and place it in the config folder.")
         return

    # Initialize Brain
    try:
        brain = GeminiBrain()
    except Exception as e:
        print(f"❌ Error initializing Gemini: {e}")
        return

    # Load sites
    with open('config/sites.json', 'r') as f:
        sites = json.load(f)
    
    for site in sites:
        print(f"\nProcessing Site: {site.get('site_name', 'Unknown')}")
        
        # Init Sheets
        try:
            sheets = SheetsClient('config/service_account.json')
            pending_keywords = sheets.get_pending_rows(site['spreadsheet_id'])
            print(f"Found {len(pending_keywords)} pending keywords.")
        except Exception as e:
            print(f"❌ Error accessing sheets for {site['site_name']}: {e}")
            continue

        # Init WordPress
        wp = WordPressClient(
            site['wordpress_url'],
            site['wordpress_username'],
            site['wordpress_app_password']
        )
        if not wp.verify_auth():
            print(f"❌ Error: Cannot authenticate with WordPress for {site['site_name']}")
            continue

        for item in pending_keywords:
            keyword = item['keyword']
            row_num = item['row_num']
            print(f"  👉 Working on: {keyword}")

            # 1. Research & Draft
            print("     Researching and Drafting (Gemini)...")
            draft = brain.research_and_draft(keyword)

            # 2. Refine (Persona)
            print("     Refining with Persona...")
            final_content = brain.refine_with_persona(draft, site['persona_prompt'])

            # 3. Images (3 Images Logic)
            print("     Generating Images (Cover + 2 Body Images)...")
            prompts_list = brain.generate_image_prompts(final_content)
            print(f"     [Prompts]: {len(prompts_list)} found.")
            
            featured_media_id = None
            
            # Loop through prompts to generate images
            # Index 0 = Cover/Featured. Index 1+ = Body.
            slug_base = keyword.replace(" ", "-").lower()[:50]
            
            for i, p_text in enumerate(prompts_list):
                print(f"     Generating Image {i+1}...")
                images_b64 = brain.generate_images(p_text)
                
                if images_b64:
                    try:
                        import base64
                        image_data = base64.b64decode(images_b64[0])
                        filename = f"{slug_base}-img{i+1}.png"
                        
                        print(f"     Uploading {filename}...")
                        media_id, media_url = wp.upload_media(image_data, filename)
                        
                        if media_id:
                            if i == 0:
                                # First image is featured
                                featured_media_id = media_id
                                print(f"     ✅ Featured Image Set (ID: {media_id})")
                            else:
                                # Other images go into content
                                # Simple insertion strategy: Append to H2s or paragraphs.
                                # Let's find the i-th H2 and insert after it.
                                # Since i starts at 1 for these (i=0 is cover), we insert i=1 after first H2, i=2 after second.
                                target_tag = "</h2>"
                                if target_tag in final_content:
                                    # Split content by H2
                                    parts = final_content.split(target_tag)
                                    # If we have enough parts, insert
                                    # Logic: parts[0] is before 1st H2. parts[1] is between 1st and 2nd.
                                    # We want to insert image AFTER the H2 closes.
                                    # So we append content to parts[i].
                                    
                                    # Note: this split logic is brittle but efficient for MVP.
                                    # We need to construct string back.
                                    
                                    # Better approach: Just find and replace occurrence `i` of </h2>
                                    # But python replace replaces all or count.
                                    
                                    # Let's do simple append if H2 not found or complex.
                                    # Actually, appending to parts is safer using `replace` with count=1 stepwise? No.
                                    
                                    # Let's go with: Insert Image 2 after 1st H2, Image 3 after 2nd H2.
                                    img_html = f'\n<figure class="wp-block-image"><img src="{media_url}" alt="{keyword} image {i+1}" class="wp-image-{media_id}"/></figure>\n'
                                    
                                    # Find the i-th occurrence of </h2>.
                                    # Since i starts at 1 here (loop enumerates 0, 1, 2).
                                    # i=1 is "Image 2". We successfully split logic.
                                    
                                    # Let's try to split by </h2>, insert image at index i, join back.
                                    # parts = [intro, section1, section2...]
                                    # target i is for parts[i] -> insert after parts[i] + </h2>
                                    
                                    parts = final_content.split(target_tag)
                                    if len(parts) > i:
                                        # parts[i] is the chunk before the (i+1)th H2? No.
                                        # "Header 1 </h2> Content"
                                        # split -> ["Header 1 ", " Content"]
                                        # We want "Header 1 </h2> <IMG> Content"
                                        
                                        # So we manipulate parts[i-1]? No, simpler:
                                        # Just search and replace the n-th occurrence?
                                        
                                        # Let's keep it simple: Append to end of content if complex parsing fails.
                                        # Or simple replacement loop.
                                        
                                        # Let's try constructing the new content only once after loop? No, content changes.
                                        
                                        # Simple heuristic:
                                        # Find first </h2>, replace with </h2><IMG>, BUT mark it so we don't replace it again?
                                        # We can replace </h2> with </h2><!--IMGDONE--> to skip?
                                        
                                        replacement = f"</h2>{img_html}"
                                        final_content = final_content.replace(target_tag, replacement, 1)
                                        print(f"     ✅ Image {i+1} inserted into content.")
                                    else:
                                         # Not enough headers, append to end
                                         final_content += img_html
                                         print(f"     ⚠️ Header not found, appending Image {i+1} to end.")
                                else:
                                    final_content += img_html
                    except Exception as img_err:
                        print(f"     ❌ Image {i+1} failed: {img_err}")

            # 4. Post to WP
            print("     Posting to WordPress...")
            user_title = keyword.title()
            try:
                post = wp.create_post(
                    title=user_title,
                    content=final_content,
                    featured_media_id=featured_media_id,
                    status='draft' # Safety first
                )
                link = post.get('link')
                print(f"     ✅ Posted! Link: {link}")
                
                # 5. Update Sheet
                sheets.update_row(site['spreadsheet_id'], row_num, link, status="Done")
                print("     ✅ Sheet updated.")
            except Exception as e:
                print(f"     ❌ Failed to post/update: {e}")

if __name__ == "__main__":
    main()
