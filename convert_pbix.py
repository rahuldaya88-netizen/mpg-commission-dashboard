import os
import zipfile
import json

def extract_and_generate_html(pbix_path, output_dir):
    # .pbix file ek zip archive hoti hai jisme Layout json hota hai
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    if not os.path.exists(pbix_path):
        print(f"Error: File nahi mili -> {pbix_path}")
        return None

    with zipfile.ZipFile(pbix_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
        print("PBIX file successfully extracted to:", output_dir)

    layout_path = os.path.join(output_dir, 'Report', 'Layout')
    
    if os.path.exists(layout_path):
        # Layout file utf-16 le encoded hoti hai
        with open(layout_path, 'r', encoding='utf-16-le') as f:
            layout_data = json.load(f)
        
        # Automatic powerbi_report.html generate karna
        sections = layout_data.get('sections', [])
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Power BI Report View</title>
            <style>
                body {{ background-color: #0B0F19; color: #E2E8F0; font-family: Segoe UI, sans-serif; padding: 20px; }}
                .page-card {{ background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                h2 {{ color: #38BDF8; }}
            </style>
        </head>
        <body>
            <h1>📊 Power BI Extracted Report Layout</h1>
            <p>Total Pages Found: {len(sections)}</p>
        """
        
        for idx, sec in enumerate(sections):
            page_name = sec.get('displayName', f'Page {idx + 1}')
            html_content += f"""
            <div class="page-card">
                <h2>📄 Page: {page_name}</h2>
                <p>Layout Name: {sec.get('name', 'N/A')}</p>
                <p>Visuals Count: {len(sec.get('visualContainers', []))}</p>
            </div>
            """
            
        html_content += "</body></html>"
        
        # Root folder mein powerbi_report.html save karein
        with open("powerbi_report.html", "w", encoding="utf-8") as html_file:
            html_file.write(html_content)
            
        print("Successfully generated powerbi_report.html!")
        return layout_data
    else:
        print("Warning: Report/Layout file nahi mili extracted folder mein.")
    return None

# Aapke Desktop par jo file hai uska path
pbix_file = r"C:\Users\rahul\Desktop\Masterfile19.pbix"
output_folder = "./pbix_extracted"

layout = extract_and_generate_html(pbix_file, output_folder)
if layout:
    print("PBIX Layout successfully extracted, loaded, and HTML generated!")
