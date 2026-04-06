export function generateGeminiSettings(denyPatterns) {
  const settings = {
    deny_rules: denyPatterns.map(p => ({ tool: 'shell', pattern: p.pattern })),
  };
  return JSON.stringify(settings, null, 2);
}

export function generateCodexConfig(denyPatterns) {
  const config = {
    deny_rules: denyPatterns.map(p => ({ tool: 'shell', pattern: p.pattern })),
  };
  return JSON.stringify(config, null, 2);
}
