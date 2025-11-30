.PHONY: setup run clean

setup:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt
	sudo apt install -y portaudio19-dev ffmpeg

run:
	./venv/bin/python main.py

clean:
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf venv
