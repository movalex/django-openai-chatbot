
# TODO
### UI
* add a good looking bootstrap sidebar
* add chats list to the sidebar
* better submit form placement on large screens

#### Sidebar elements as seen by the user
- top of the sidebar is the chatlist with just api requests
    * each chat list element have its own settings inside the nav bar (change the model is possible during the current chat session)
- Assistant name (with settings button)
    * chat name
        - each element of the chat list is determined by the assistant settings
        - change model and the knowledge base is only allowed on assistand level, no model settings in the nav bar
- bottom of the sidebar is user settings and logiut button
- Submit form in the assistants chat has attach     button for fiel uploading
- Assistant settings:
    * Instructions text field
    * Knowledge base file upload section
    * functions text field

### API
* auto-rename the chat lists
* add assistants API handling
    - assistant elements to the sidebar as parent elemet of the chat list
    - assistant chat settings are determined by assistant settings
    - add assistant instructions and functions calling
* allow choose between normal chat and the assistant


### Chat formatting improvements
* add use 2spaces tab length markdown rule for nested lists:
    - example:
    ```python
    markdown.markdown(text, tab_length=2)
    ```