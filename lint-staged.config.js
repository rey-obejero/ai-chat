export default {
  "back-end/**/*.py": ["ruff check --fix", "ruff format"],
  "front-end/**/*.{vue,ts,js,css}": ["eslint --fix", "prettier --write"],
};
