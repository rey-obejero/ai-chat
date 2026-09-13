const stripPrefix = (prefix) => (files) =>
  files.map((file) => file.replace(new RegExp(`^${prefix}/`), ''));

export default {
  "back-end/**/*.py": (files) => [
    `back-end/.venv/bin/ruff check --fix ${files.join(" ")}`,
    `back-end/.venv/bin/ruff format ${files.join(" ")}`,
  ],
  "front-end/**/*.{vue,ts,js,css}": (files) => [
    `pnpm --dir front-end exec eslint --fix ${stripPrefix("front-end")(files).join(" ")}`,
    `pnpm --dir front-end exec prettier --write ${stripPrefix("front-end")(files).join(" ")}`,
  ],
};
