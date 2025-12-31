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
            import traceback
            traceback.print_exc()
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

            user_title = keyword.title()
            # 3. Images (Stubbed - Now Active)
            print("     Generating Images...")
            image_prompt = brain.generate_image_prompts(final_content)
            images_b64 = brain.generate_images(image_prompt)
            print(f"     [Image Generated]: {len(images_b64)} images")
            
            featured_media_id = None
            if images_b64:
                 try:
                     import base64
                     
                     print(f"     Processing {len(images_b64)} images...")
                     
                     # Define slug for filenames
                     slug = keyword.replace(" ", "-").lower()[:50]
                     
                     for i, b64_str in enumerate(images_b64):
                         image_data = base64.b64decode(b64_str)
                         
                         suffix = "cover" if i == 0 else f"image-{i+1}"
                         filename = f"{slug}-{suffix}.png"
                         
                         print(f"     Uploading Image {i+1}/{len(images_b64)} ({filename})...")
                         media_id, media_url = wp.upload_media(image_data, filename)
                         
                         if media_id:
                             if i == 0:
                                 featured_media_id = media_id
                                 print(f"     ✅ Set as Featured Image (ID: {media_id})")
                             else:
                                 # Append to content
                                 # Add a little spacing
                                 final_content += f"\n\n<!-- Image {i+1} -->\n<figure class='wp-block-image size-large'><img src='{media_url}' alt='{user_title} - Image {i+1}'/></figure>"
                                 print(f"     ✅ Inserted into content (ID: {media_id})")
                                 
                 except Exception as img_err:
                     print(f"     ❌ Image processing failed: {img_err}")

            # 4. Post to WP
            print("     Posting to WordPress...")
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
