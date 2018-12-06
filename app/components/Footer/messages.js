/*
 * Footer Messages
 *
 * This contains all the text for the Footer component.
 */
import { defineMessages } from 'react-intl';

export default defineMessages({
  licenseMessage: {
    id: 'boilerplate.components.Footer.license.message',
    defaultMessage: '',
  },
  authorMessage: {
    id: 'boilerplate.components.Footer.author.message',
    defaultMessage: `
      Made with React-Boilerplate by {author}
    `,
  },
  hostedByMessage: {
    id: 'boilerplate.components.Footer.hostedBy.message',
    defaultMessage: `
      Hosted on {hostedBy}.
    `,
  },
});
