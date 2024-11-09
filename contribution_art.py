import sys
import subprocess
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import pytz

def purge_dummy_commits():
    """
    Purge all dummy commits created by this script using a non-interactive rebase.
    This will remove commits with the message "Contribution art".
    """
    try:
        # Use a non-interactive rebase to delete specific commits by resetting them
        subprocess.run([
            "git", "rebase", "--root", "--exec",
            "git reset $(git rev-list --all --grep 'Contribution art')"
        ], check=True)

        # Push with force to overwrite history on the remote
        subprocess.run(["git", "push", "--force", "origin", "main"], check=True)
    except subprocess.CalledProcessError as e:
        print("Error during purge:", e)

def create_commit(date, commit_count):
    """
    Create a specified number of commits on a specific date.
    """
    for _ in range(commit_count):
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Contribution art"],
            env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
        )

def get_resized_font(text, max_height, max_width, initial_font_size=10):
    font_size = initial_font_size
    font = ImageFont.load_default()
    while True:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

        text_bbox = font.getbbox(text)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        if text_height > max_height or text_width > max_width:
            font_size -= 1
            break
        font_size += 1
    return font

def generate_text_grid(text):
    max_height = 7
    max_width = 100
    font = get_resized_font(text, max_height, max_width)

    text_bbox = font.getbbox(text)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

    image_width = min(text_width, max_width)
    image = Image.new("L", (image_width, max_height), 255)
    draw = ImageDraw.Draw(image)
    draw.text(((image_width - text_width) // 2, (max_height - text_height) // 2), text, fill=0, font=font)
    return image

def generate_image_grid(image_path):
    image = Image.open(image_path).convert("L")
    image = image.resize((100, 7), Image.ANTIALIAS)
    return image

def brightness_to_commits(brightness, max_commits=5):
    normalized_intensity = 255 - brightness
    return int((normalized_intensity / 255) * max_commits)

def map_pixel_to_date(x, y, width, start_date):
    days_offset = x * 7 + y
    return start_date + timedelta(days=days_offset)

def main(input_type, content):
    purge_dummy_commits()

    if input_type == "text":
        grid = generate_text_grid(content)
    elif input_type == "image":
        grid = generate_image_grid(content)
    else:
        raise ValueError("Invalid input type. Use 'text' or 'image'.")

    start_date = datetime.now() - timedelta(days=365)

    for x in range(grid.width):
        for y in range(grid.height):
            brightness = grid.getpixel((x, y))
            commit_count = brightness_to_commits(brightness)

            if commit_count > 0:
                commit_date = map_pixel_to_date(x, y, grid.width, start_date).strftime("%Y-%m-%dT12:00:00")
                create_commit(commit_date, commit_count)

    subprocess.run(["git", "push", "--force", "origin", "main"])

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python contribution_art.py <text|image> <content>")
        sys.exit(1)

    input_type = sys.argv[1]
    content = sys.argv[2]
    main(input_type, content)

