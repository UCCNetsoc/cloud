import ModalTop from "./ModalTop";

const Dialog = (props: { children: React.ReactNode }) => {
  return (
    <>
      <ModalTop />
      {props.children}
    </>
  )
}

export default Dialog;
