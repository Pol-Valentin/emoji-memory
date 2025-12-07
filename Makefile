PLUGIN_ID = com_pol_emoji_memory
FLATPAK_PATH = $(HOME)/.var/app/com.core447.StreamController/data/plugins/$(PLUGIN_ID)
NATIVE_PATH = $(HOME)/.config/streamcontroller/plugins/$(PLUGIN_ID)

.PHONY: link uninstall clean status download-emojis install

# Symlink for development (recommended)
link:
	@if [ -d "$(FLATPAK_PATH)" ] || [ -L "$(FLATPAK_PATH)" ]; then \
		rm -rf "$(FLATPAK_PATH)"; \
	fi
	ln -sf "$(PWD)" "$(FLATPAK_PATH)"
	@echo "Linked to $(FLATPAK_PATH)"

# Copy installation
install:
	@if [ -d "$(FLATPAK_PATH)" ] || [ -L "$(FLATPAK_PATH)" ]; then \
		rm -rf "$(FLATPAK_PATH)"; \
	fi
	cp -r "$(PWD)" "$(FLATPAK_PATH)"
	@echo "Installed to $(FLATPAK_PATH)"

# Remove plugin
uninstall:
	rm -rf "$(FLATPAK_PATH)"
	rm -rf "$(NATIVE_PATH)"
	@echo "Plugin removed"

# Clean cache and pycache
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cache cleaned"

# Check installation status
status:
	@if [ -L "$(FLATPAK_PATH)" ]; then \
		echo "Linked (dev mode): $(FLATPAK_PATH) -> $$(readlink $(FLATPAK_PATH))"; \
	elif [ -d "$(FLATPAK_PATH)" ]; then \
		echo "Installed (copy): $(FLATPAK_PATH)"; \
	else \
		echo "Not installed"; \
	fi

# Download all animated emojis
download-emojis:
	python3 download_emojis.py
	@echo "Emojis downloaded to assets/emojis/"
