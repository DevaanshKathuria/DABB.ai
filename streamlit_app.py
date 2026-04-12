"""Default Streamlit Community Cloud entrypoint."""

from app import render_app


def main() -> None:
    """Launch the Streamlit app."""
    render_app()


if __name__ == "__main__":
    main()
