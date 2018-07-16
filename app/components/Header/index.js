import React from 'react';
import { FormattedMessage } from 'react-intl';
import { bounce, zoomIn } from 'react-animations';
import Radium, { StyleRoot } from 'radium';

import A from './A';
import Img from './Img';
import NavBar from './NavBar';
import HeaderLink from './HeaderLink';
import Banner from './WestCoastSoftware_Mirrored_Logo_940x280_Pixels_NoDepth-500x144.jpg';
import messages from './messages';

const styles = {
  bounce: {
    animation: 'x 1s',
    animationName: Radium.keyframes(bounce, 'bounce'),
  },
  zoomIn: {
    animation: 'x 1s',
    animationName: Radium.keyframes(zoomIn, 'zoomIn'),
  },
};


class Header extends React.Component { // eslint-disable-line react/prefer-stateless-function
  render() {
    return (
      <div>
        <StyleRoot>
          <div style={styles.zoomIn}>
            <A href="http://www.westcoastsoftware.com/">
              <Img src={Banner} alt="react-boilerplate - Logo" />
            </A>
          </div>
        </StyleRoot>
        <NavBar>
          <HeaderLink to="/">
            <FormattedMessage {...messages.home} />
          </HeaderLink>
          <HeaderLink to="/features">
            <FormattedMessage {...messages.features} />
          </HeaderLink>
        </NavBar>
      </div>
    );
  }
}

export default Header;
