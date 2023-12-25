from gooey import Gooey, GooeyParser
from time import sleep
import sys

@Gooey(program_name="NSFW Download App", menu=[{"name": "About", "items": [{
    'type': 'MessageDialog',
    'menuTitle': 'Version',
    'message': 'It is 3.0.0-ALPHA (Dev at 2023-11-22)',
    'caption': 'Version'
},
{
    'type': 'MessageDialog',
    'menuTitle': 'Updates',
    'message': 'Currently there is empty.',
    'caption': 'Updates'
}]}],
    progress_regex=r"^progress: (\d+)%$",
    timing_options = {
        'show_time_remaining':True,
        'hide_time_remaining_on_complete':True,
    })
def main():
    parser = GooeyParser()
    entities = parser.add_argument_group("Info About Entity", "Enter some information about your entity you wanna to download")
    # Text box for entering a text (Entity tag)
    entities.add_argument('entity_tag', help='Entity tag', widget='TextField')

    # Radio group for selecting between "All," "Videos," "Images," and "Animations"
    grp = entities.add_argument_group("Media format")
    grp.add_argument('--media_type', help='Select media type', choices=['All', 'Videos', 'Images', 'Animations'], widget='Dropdown', default='All')


    # Checkbox for enabling page selection
    parser.add_argument('--enable_page_selection', help='Enable page selection', action='store_true', default=False, widget='CheckBox')

    # Page selection group (conditional on whether the checkbox is checked)
    page_selection_group = parser.add_argument_group('Page Selection', gooey_options={'show_border': True})

    # Add arguments for page selection if the checkbox is checked
    if parser.parse_args().enable_page_selection:
        page_selection_group.add_argument('--start_page', help='Start page', type=int)
        page_selection_group.add_argument('--end_page', help='End page', type=int)

    args = parser.parse_args()

    # Your application logic using the 'args' namespace
    for i in range(100):
        print("progress: {}%".format(i + 1))
        sys.stdout.flush()
        sleep(0.1)

    print(f"You are going to download {args.entity_tag}")

if __name__ == "__main__":
    main()
