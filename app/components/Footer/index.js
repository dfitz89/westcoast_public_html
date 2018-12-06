import React from 'react';
import { FormattedMessage } from 'react-intl';

import A from 'components/A';
import Wrapper from './Wrapper';
import messages from './messages';

function Footer() {
  return (
    <Wrapper>
      <section><FormattedMessage {...messages.licenseMessage} /></section>
      <section>
        <FormattedMessage
          {...messages.authorMessage}
          values={{ author: <A href="http://www.westcoastsoftware.com/">West Coast Software</A> }}
        />
        <FormattedMessage
          {...messages.hostedByMessage}
          values={{ hostedBy: <A href="http://www.amazonaws.com/">Amazon Web Services</A> }}
        />
      </section>
    </Wrapper>
  );
}

export default Footer;
