import {
  createIcons,
  LogOut,
  MessageCircle,
  Mic,
  PanelLeft,
  Pause,
  Play,
  Plus,
  ArrowUp,
} from "lucide";

const icons = {
  LogOut,
  MessageCircle,
  Mic,
  PanelLeft,
  Pause,
  Play,
  Plus,
  ArrowUp,
};

window.refreshIcons = () => {
  createIcons({
    attrs: {
      "aria-hidden": "true",
      "stroke-width": 1.8,
    },
    icons,
  });
};

window.refreshIcons();
