import Handlebars from 'handlebars';

export function renderTemplate(templateString, data) {
  const compiled = Handlebars.compile(templateString, { noEscape: true });
  return compiled(data);
}
