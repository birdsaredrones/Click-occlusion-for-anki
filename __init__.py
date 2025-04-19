from aqt import mw
from aqt.qt import QAction
from .editor import launch_editor
from aqt.utils import showInfo
from anki.models import NoteType
import atexit

def create_note_type_if_needed():
    name = "Click Occlusion"
    models = mw.col.models
    existing = models.byName(name)
    
    if existing:
        return  # Already exists

    # Create a new model
    model = models.new(name)

    # Add fields
    for field_name in ["Image", "Answer", "Header"]:
        models.addField(model, models.newField(field_name))

    # Add a card template
    template = {
        'name': 'Card 1',
        'qfmt': '''
        <div style="font-weight: bold; margin-bottom: 10px;">{{Header}}</div>
        <div class="occlusion-container">
          {{Image}}
        </div>


        <script>
        document.querySelectorAll(".clickbox").forEach(box => {
          box.onclick = () => box.style.visibility = "hidden";
        });
        </script>

        <style>
          .occlusion-container {
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: auto;
          }

          .occlusion-container img {
            max-width: 100%;
            height: auto;
          }

          .clickbox {
            position: absolute;

            /*                    */
                /* CHANGE COLOUR HERE */
           /*                    */
            background-color: rgba(245, 121, 39, 1);
           /*                    */
           /*                    */

            cursor: pointer;
            visibility: visible;
          }
        </style>


        ''',
        'afmt': '''

        <div style="font-weight: bold; margin-bottom: 10px;">{{Header}}</div>
        <div class="occlusion-wrapper">
          {{Image}}
        </div>
        <div class="occlusion-text">
          {{Answer}}
        </div>

        <style>
          .occlusion-wrapper {
            display: inline-block;
            position: relative;
          }

          .occlusion-wrapper img {
            display: block;
            max-width: 100%;
            height: auto;
          }

          .occlusion-text {
            margin-top: 10px;
          }

          .clickbox {
            display: none; /* ensure they're hidden on the back */
          }
        </style>

        ''',
    }
    model['tmpls'].append(template)

    # Add the model to the collection
    models.add(model)
    models.save(model)

    showInfo(f"Note type '{name}' was created!")

# Run it after Anki is fully loaded
atexit.register(create_note_type_if_needed)


def add_click_occlusion():
    launch_editor()

action = QAction("Click Image Occlusion", mw)
action.triggered.connect(add_click_occlusion)
mw.form.menuTools.addAction(action)