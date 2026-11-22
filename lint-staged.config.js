const stripPrefix = (prefix) => (files) =>
  files.map((file) => file.replace(new RegExp(`^${prefix}/`), ''));

export default {
  "backend/**/*.py": (files) => [
    `backend/.venv/bin/ruff check --fix ${files.join(" ")}`,
    `backend/.venv/bin/ruff format ${files.join(" ")}`,
  ],
  "frontend/**/*.{vue,ts,js,css}": (files) => [
    `pnpm --dir frontend exec eslint --fix ${stripPrefix("frontend")(files).join(" ")}`,
    `pnpm --dir frontend exec prettier --write ${stripPrefix("frontend")(files).join(" ")}`,
  ],
};
