<p align="center">
  <img src="https://wsrv.nl/?url=https://i.ibb.co/YTDpg0gZ/prgif.gif&output=webp&n=-1&maxage=1y" alt="PyQT_C.AI Logo" width="200"/>
</p>

# CharacterAI Chatbot - PyQt5 🤖💬

CharacterAI chatbot with GUI using PyQt5. Enjoy a rich and interactive chatting experience with markdown support, persistent chat history, and optional voice output powered by **PyCharacterAI** and **characterai** libraries.

## ✨ Key Features

*   **Intuitive UI:** A user-friendly PyQt5 interface for seamless chatting.
*   **Markdown:** AI responses are rendered with full markdown support, including code snippets and formatted text.
*   **Chat History:** Conversations are automatically saved and restored for continuous interaction.
*   **Voice Output (Optional):** Enable voice output to hear the AI's responses using the power of PyCharacterAI (requires setup).
*   **Dark Mode Support:** Switch to a dark theme for comfortable late-night chatting.

## 🚀 Getting Started

### Prerequisites

*   Python 3.7+
*   [Character AI Account](https://character.ai/) (for API access)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/SSL-ACTX/PyQT_C.AI.git
    cd PyQT_C.AI
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  **Edit `config.ini`:**  This file holds your Character AI credentials. **IMPORTANT:** Do not commit your actual token and character ID to a public repository!
    ```ini
    [DEFAULT]
    token = YOUR_CHARACTERAI_TOKEN  ; See aiocai's docs
    char_id = YOUR_CHARACTER_ID       ; See aiocai's docs
    ```

### Running the Chatbot

1.  **Start the application:**
    ```bash
    python main.py
    ```

    *   **Dark Mode:** To launch the chatbot in dark mode, use:
        ```bash
        python main.py --dark
        ```

## 🗣️ Enabling Voice Output (Optional)

1.  **Ensure PyCharacterAI is configured:** The script leverages PyCharacterAI for voice generation. Double-check its installation and setup instructions (see [PyCharacterAI Repository](https://github.com/Xtr4F/PyCharacterAI)).
2.  **Enable the "Voice Output" toggle** within the chatbot interface.

**Note:** Voice output requires a valid Character AI token and relies on the capabilities of PyCharacterAI.

## 🖼️ Screenshots

<p align="center">
  <img src="https://wsrv.nl/?url=https://i.ibb.co/G4xKMV7Q/image.png&output=webp&q=80&maxage=1y" alt="Light Mode" width="300"/>
  <img src="https://wsrv.nl/?url=https://i.ibb.co/7NBp3t53/image.png&output=webp&q=80&maxage=1y" alt="Dark Mode" width="300"/>
</p>

## 🤝 Contributing

Contributions are welcome!  Feel free to submit pull requests with improvements, bug fixes, or new features.  Please follow the existing code style and include appropriate tests.

## 📝 License

[MIT License](LICENSE)

## ⭐️ Like it?

If you find this project cool, please consider giving it a star ⭐.
