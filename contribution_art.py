import sys
import subprocess
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

def purge_dummy_commits():
    """
    Purge only the dummy commits created by this script.
    This function will remove commits with the message "Contribution art".
    """
    # Use git filter-branch to remove commits with the specific message
    try:
        subprocess.run([
            "git", "filter-branch", "--force", "--msg-filter",
            'grep -v "Contribution art"'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print("Error during purge:", e)

def create_commit(date, commit_count):
    """
    Create a specified number of commits on a specific date.
    """
    for _ in range(commit_count):
        subprocess.run(["git", "commit", "--allow-empty", "-m", "Contribution art"], env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})

def get_resized_font(text, max_height, max_width, initial_font_size=10):
    """
    Dynamically resize font to fit within the given max height and max width.
    """
    font_size = initial_font_size
    font = ImageFont.load_default()
    while True:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)  # Adjust this if Arial is not available on your system
        except OSError:
            font = ImageFont.load_default()  # Default font if TTF not found

        # Use getbbox to measure text width and height
        text_bbox = font.getbbox(text)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        if text_height > max_height or text_width > max_width:
            font_size -= 1  # Reduce font size if text is too big
            break
        font_size += 1  # Incrementally increase font size to fit within the dimensions
    return font

def generate_text_grid(text):
    """
    Generate a grayscale grid pattern based on dynamically resized text input.
    """
    max_height = 7
    max_width = 100
    font = get_resized_font(text, max_height, max_width)
    text_width, text_height = font.getsize(text)

    # Create an image sized to the text width but limited to 100x7 for the GitHub grid
    image_width = min(text_width, max_width)
    image = Image.new("L", (image_width, max_height), 255)  # Grayscale image with white background
    draw = ImageDraw.Draw(image)
    draw.text(((image_width - text_width) // 2, (max_height - text_height) // 2), text, fill=0, font=font)  # Center text
    return image

def generate_image_grid(image_path):
    """
    Generate a grayscale grid pattern from an image input.
    """
    image = Image.open(image_path).convert("L")  # Convert to grayscale
    image = image.resize((100, 7), Image.ANTIALIAS)  # Resize to 100x7 grid for the GitHub contribution chart
    return image

def brightness_to_commits(brightness, max_commits=5):
    """
    Map brightness (0-255) to a commit count (0-max_commits).
    Darker pixels (lower brightness) result in more commits.
    """
    normalized_intensity = 255 - brightness
    return int((normalized_intensity / 255) * max_commits)

def main(input_type, content):
    # Purge only dummy commits to start with a clean slate for this run
    purge_dummy_commits()

    # Generate the bitmap pattern
    if input_type == "text":
        grid = generate_text_grid(content)
    elif input_type == "image":
        grid = generate_image_grid(content)
    else:
        raise ValueError("Invalid input type. Use 'text' or 'image'.")

    # Calculate the start date (last year from today)
    start_date = datetime.now() - timedelta(days=365)

    # Traverse the grid and create commits based on the pattern
    for x in range(grid.width):
        for y in range(grid.height):
            brightness = grid.getpixel((x, y))  # Get pixel brightness (0-255)
            commit_count = brightness_to_commits(brightness)

            if commit_count > 0:  # Only create commits for non-white (non-empty) pixels
                date = start_date + timedelta(days=(x * 7 + y))
                commit_date = date.strftime("%Y-%m-%dT12:00:00")  # Format date for git
                create_commit(commit_date, commit_count)

    # Finalize by pushing the commits
    subprocess.run(["git", "push", "origin", "main"])

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python contribution_art.py <text|image> <content>")
        sys.exit(1)

    input_type = sys.argv[1]
    content = sys.argv[2]
    main(input_type, content)

