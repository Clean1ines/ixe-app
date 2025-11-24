"""
Script to debug extract_block_pairs function with real HTML from FIPI.
"""
import sys
from pathlib import Path

# Add src to path so we can import the module
sys.path.insert(0, str(Path(".").resolve()))

from src.domain.html_processing.pure_html_transforms import extract_block_pairs

def debug_with_real_html():
    # Load HTML content from a file or use a sample
    # For now, we'll use a simplified version that mimics the structure from the pasted HTML
    # In the provided HTML fragments, we can see multiple qblock elements
    # Let's create a test HTML that has the common context followed by individual qblocks
    html_content = """
    <html>
    <body>
        <!-- Common qblock without ID - contains shared context -->
        <div class="qblock">
            <div class="cell_0">Прочитайте текст и выполните задания 1-27.</div>
        </div>
        
        <!-- Individual qblocks with IDs -->
        <div class="qblock" id="q4D1A4B">
            <div class="task-header-panel">
                <span class="id-text"><span class="canselect">1</span></span>
            </div>
            <div class="cell_0">Задание 1.</div>
        </div>
        
        <div class="qblock" id="q005141">
            <div class="task-header-panel">
                <span class="id-text"><span class="canselect">2</span></span>
            </div>
            <div class="cell_0">Задание 2.</div>
        </div>
        
        <div class="qblock" id="qFE2041">
            <div class="task-header-panel">
                <span class="id-text"><span class="canselect">3</span></span>
            </div>
            <div class="cell_0">Задание 3.</div>
        </div>
        
        <div class="qblock" id="q047D4B">
            <div class="task-header-panel">
                <span class="id-text"><span class="canselect">4</span></span>
            </div>
            <div class="cell_0">Задание 4.</div>
        </div>
        
        <div class="qblock" id="q462A4A">
            <div class="task-header-panel">
                <span class="id-text"><span class="canselect">5</span></span>
            </div>
            <div class="cell_0">Задание 5.</div>
        </div>
        
        <div class="qblock" id="q4E5B4C">
            <div class="task-header-panel">
                <span class="id-text"><span class="canselect">6</span></span>
            </div>
            <div class="cell_0">Задание 6.</div>
        </div>
        
        <div class="qblock" id="q445A48">
            <div class="task-header-panel">
                <span class="id-text"><span class="canselect">7</span></span>
            </div>
            <div class="cell_0">Задание 7.</div>
        </div>
        
        <div class="qblock" id="q003B4D">
            <div class="task-header-panel">
                <span class="id-text"><span class="canselect">8</span></span>
            </div>
            <div class="cell_0">Задание 8.</div>
        </div>
        
        <div class="qblock" id="qFE9149">
            <div class="task-header-panel">
                <span class="id-text"><span class="canselect">9</span></span>
            </div>
            <div class="cell_0">Задание 9.</div>
        </div>
        
        <div class="qblock" id="q4D1A4B">
            <div class="task-header-panel">
                <span class="id-text"><span class="canselect">10</span></span>
            </div>
            <div class="cell_0">Задание 10.</div>
        </div>
    </body>
    </html>
    """
    
    print("Input HTML has a common qblock followed by 10 individual qblocks with IDs")
    pairs = extract_block_pairs(html_content)
    print(f"extract_block_pairs returned {len(pairs)} pairs")
    
    for i, (header, body) in enumerate(pairs):
        print(f"Pair {i+1}: Header contains ID: {'id="i' in header}")
        # Check if body contains multiple qblocks (indicating grouping worked)
        qblock_count_in_body = body.count('<div class="qblock"')
        print(f"Pair {i+1}: Body contains {qblock_count_in_body} individual qblocks")
        if qblock_count_in_body > 1:
            print(f"Pair {i+1}: Grouping worked! Body combines multiple qblocks.")
        print("---")

if __name__ == "__main__":
    debug_with_real_html()
