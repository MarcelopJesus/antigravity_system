import json
import os
import base64
from core.gemini_brain import GeminiBrain
from core.sheets_client import SheetsClient
from core.wordpress_client import WordPressClient

def main():
    print("🚀 SEO Orchestrator (Multi-Tenant Architecture) Starting...")
    
    # Check for service account
    if not os.path.exists('config/service_account.json'):
         print("❌ Error: 'config/service_account.json' missing.")
         return

    # Load sites configuration
    with open('config/sites.json', 'r') as f:
        sites = json.load(f)
    
    for site in sites:
        company_id = site.get('company_id', 'default')
        site_name = site.get('site_name', 'Unknown')
        
        print(f"\n{'='*80}")
        print(f"🏢 Processing Company: {site_name} (ID: {company_id})")
        print(f"{'='*80}")
        
        # Initialize Brain with company-specific knowledge base
        kb_path = f"config/companies/{company_id}/knowledge_base"
        try:
            brain = GeminiBrain(knowledge_base_path=kb_path)
            print(f"✅ Brain initialized for '{company_id}' with KB path: {kb_path}")
        except Exception as e:
            print(f"❌ Error initializing Gemini for '{company_id}': {e}")
            continue
        
        # Init Sheets
        try:
            sheets = SheetsClient('config/service_account.json')
            pending_keywords = sheets.get_pending_rows(site['spreadsheet_id'])
            
            # Fetch Inventory for Internal Linking
            print("     Fetching Article Inventory for Link Building...")
            inventory = sheets.get_all_completed_articles(site['spreadsheet_id'])
            print(f"     Found {len(inventory)} existing articles to potential link to.")
            
            print(f"Found {len(pending_keywords)} pending keywords to write.")
        except Exception as e:
            print(f"❌ Error accessing sheets: {e}")
            continue

        # Init WordPress
        wp = WordPressClient(
            site['wordpress_url'],
            site['wordpress_username'],
            site['wordpress_app_password']
        )
        if not wp.verify_auth():
            print(f"❌ Error: Cannot authenticate with WordPress.")
            continue

        for item in pending_keywords:
            keyword = item['keyword']
            row_num = item['row_num']
            print(f"\n👉 Working on Keyword: {keyword}")

            try:
                # ---------------------------------------------------------
                # STEP 1: ANALYST (Plan & Structure)
                # ---------------------------------------------------------
                print("     1. Analyst Agent: Creating Strategic Outline...")
                outline_json = brain.analyze_and_plan(keyword, inventory)
                final_title = outline_json.get('title', keyword.title())
                print(f"        Title Idea: {final_title}")

                # ---------------------------------------------------------
                # STEP 2: WRITER (Drafting)
                # ---------------------------------------------------------
                print("     2. Senior Writer Agent: Writing Content...")
                draft_html = brain.write_article_body(outline_json)

                # ---------------------------------------------------------
                # STEP 3: EDITOR (Conversion & Polishing)
                # ---------------------------------------------------------
                print("     3. Editor Agent: Polishing & SEO Local Check...")
                final_content = brain.edit_and_refine(draft_html)

                # ---------------------------------------------------------
                # STEP 4: VISUAL (Images)
                # ---------------------------------------------------------
                print("     4. Visual Agent: Generating & Processing Images...")
                prompts_str = brain.generate_image_prompts(final_content)
                
                # Split prompts safely
                prompts_list = [p.strip() for p in prompts_str.split('|||') if p.strip()]
                
                featured_media_id = None
                
                # We will process up to 3 images
                for i, prompt in enumerate(prompts_list[:3]):
                    print(f"        Generating Image {i+1}...")
                    b64_image = brain.generate_final_images(prompt)
                    
                    if b64_image:
                        image_data = base64.b64decode(b64_image)
                        slug = keyword.replace(" ", "-").lower()[:30]
                        filename = f"{slug}-{i+1}.png"
                        
                        media_id, media_url = wp.upload_media(image_data, filename)
                        
                        if i == 0:
                            featured_media_id = media_id
                            print(f"        ✅ Featured Image Set (ID: {media_id})")
                        else:
                            # Try to replace placeholders or append
                            if "<!-- IMG_PLACEHOLDER -->" in final_content:
                                final_content = final_content.replace(
                                    "<!-- IMG_PLACEHOLDER -->", 
                                    f"<figure class='wp-block-image'><img src='{media_url}' alt='{final_title} - Imagem {i+1}'/></figure>", 
                                    1
                                )
                                print(f"        ✅ Image injected into placeholder.")
                            else:
                                # Fallback append
                                final_content += f"\n<figure class='wp-block-image'><img src='{media_url}' alt='{final_title}'/></figure>"
                                print(f"        ✅ Image appended to end.")

                # ---------------------------------------------------------
                # POST TO WORDPRESS
                # ---------------------------------------------------------
                print("     Posting to WordPress (PUBLISH)...")
                
                # Extract meta description from plan (or fallback to intro snippet)
                meta_desc = outline_json.get('meta_description', "")
                if not meta_desc:
                     # Fallback: Clean HTML tags from first 160 chars of content
                     import re
                     clean = re.sub('<[^<]+?>', '', final_content)
                     meta_desc = clean[:155] + "..."

                post = wp.create_post(
                    title=final_title,
                    content=final_content,
                    featured_media_id=featured_media_id,
                    status='publish',
                    yoast_keyword=keyword,
                    yoast_meta_desc=meta_desc
                )
                link = post.get('link')
                print(f"     ✅ POSTED SUCCESSFULLY! Link: {link}")

                # Update Sheet
                sheets.update_row(site['spreadsheet_id'], row_num, link, status="Done")

                # ---------------------------------------------------------
                # STEP 5: GROWTH HACKER (New Topics)
                # ---------------------------------------------------------
                print("     5. Growth Hacker Agent: Suggesting new topics...")
                new_topics = brain.identify_new_topics(final_title, final_content)
                for topic in new_topics:
                    print(f"        💡 New Idea: {topic}")
                    sheets.add_new_topic(site['spreadsheet_id'], topic)

            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"     ❌ FAILED process keyword '{keyword}': {e}")
                # Optional: Update sheet with Error status

if __name__ == "__main__":
    main()
