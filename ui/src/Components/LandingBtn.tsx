import React from "react";
import { Link } from "react-router-dom";

import styles from './LandingBtn.module.css';

const LandingBtn = (props: { icon: React.ReactNode, name: string, url: string, small?: string, disabled?: boolean }) => {
  return (
    <li style={{ listStyleType: "none" }}>
      <Link className={styles.button} to={props.disabled ? "#" : props.url} style={{
        display: "flex",
        cursor: props.disabled ? "not-allowed" : "pointer",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        color: props.disabled ? "gray" : "white",
        textDecoration: "none",
        margin: "0.4em 1.6em",
        fontSize: "1.4em",
        userSelect: "none",
      }} draggable={false} >
        <div>
          {props.icon}
        </div>
        <div>
          {props.name}
        </div>
        <div style={{ fontSize: "0.8em", height: "1em" }}>
          {props.small}
        </div>
      </Link>
    </li>
  )
}

export default LandingBtn;