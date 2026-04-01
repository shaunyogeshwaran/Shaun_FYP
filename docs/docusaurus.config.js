import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'AFLHR Lite',
  tagline: 'Confidence-Weighted CONLI for Hallucination Detection',
  favicon: 'img/favicon.ico',

  future: { v4: true },

  url: process.env.DOCS_URL || 'http://localhost:4000',
  baseUrl: '/',

  onBrokenLinks: 'warn',

  i18n: { defaultLocale: 'en', locales: ['en'] },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          routeBasePath: 'docs',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {
        defaultMode: 'dark',
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: 'AFLHR Lite',
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'mainSidebar',
            position: 'left',
            label: 'Documentation',
          },
          {
            href: process.env.APP_URL || 'http://localhost:5173',
            label: '← Back to App',
            position: 'right',
          },
          {
            href: 'https://github.com/shaunyogeshwaran/Shaun_FYP',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        copyright: `AFLHR Lite — Shaun Yogeshwaran · BSc Computer Science · University of Westminster / IIT`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['bash', 'json'],
      },
    }),
};

export default config;
