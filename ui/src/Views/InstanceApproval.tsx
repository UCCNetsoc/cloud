import { Button, Code, Modal, Text, Textarea } from "@mantine/core";
import { showNotification } from "@mantine/notifications";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ApproveInstanceRequest, DenyInstanceRequest } from "../api/instance_request";
import { GetTemplateById } from "../api/template";
import ModalTop from "../Components/ModalTop";
import { Cloud } from "../types";

const InstanceApproval = () => {
  const { username, hostname, token, type } = useParams();
  const [loading, setLoading] = useState(true)
  const [payload, setPayload] = useState<any | null>(null)

  const [templateId, setTemplateId] = useState<string | null>(null)
  const [template, setTemplate] = useState<Cloud.Template | null>(null)

  useEffect(() => {
    if (token && loading) {
      setLoading(false)
      const payload_base64 = token?.split(".")[1];
      if (payload_base64) {
        var base64 = payload_base64.replace(/-/g, '+').replace(/_/g, '/');

        const bruh = JSON.parse(decodeURIComponent(window.atob(base64).split('').map((c) => {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join('')))
        setPayload(bruh)
        return
      }
    }
  }, [loading])

  useEffect(() => {
    if (payload && payload.detail.template_id) {
      setTemplateId(payload.detail.template_id)
    }
  }, [payload])

  useEffect(() => {
    if (templateId) {
      GetTemplateById(type as Cloud.Type, templateId).then((tpl) => {
        setTemplate(tpl)
      }).catch((_e) => {
        console.error("Couldn't get template")
      })
    }
  }, [templateId])

  return (
    <>
      <Modal size="lg" opened={true} onClose={() => { window.location.href = "/" }}>
        <ModalTop />
        <div
          style={{ width: "90%", height: "80vh", margin: "auto", paddingTop: "20px", display: "flex", flexDirection: "column" }}
        >
          <h1>
            {type?.toUpperCase()} Instance Request
          </h1>
          <Text size="lg">
            {username} is requesting {type == "lxc" ? "an LXC" : "a VPS"} instance named {hostname}
          </Text>

          <Code>
            {JSON.stringify(payload)}
          </Code>

          {template ? (
            <section style={{ marginTop: "2em", marginBottom: 0 }}>
              <div style={{ display: "flex", alignItems: "center" }}>
                <img style={{ height: "72px", width: "auto" }} src={template.metadata.logo_url} alt={`${template.metadata.title} logo`} />

                <div style={{ marginLeft: "1em", display: "flex", flexDirection: "column", justifyContent: "center" }}>
                  <h2 style={{ margin: 0 }}>{template.metadata.title}</h2>
                  <p style={{ marginTop: 0 }}>{template?.specs.cores} CPU, {template?.specs.memory} RAM, {template?.specs.disk_space}</p>
                </div>
              </div>

              <Textarea sx={{ marginTop: "2em" }} disabled value={payload.detail.reason} minRows={5} />

              <nav style={{ margin: "2em auto", width: "60%", display: "flex", alignContent: "center", justifyContent: "space-evenly" }}>
                <Button color="green" onClick={() => {
                  ApproveInstanceRequest(payload.username, hostname as string, payload.type as Cloud.Type, token as string).then((resp) => {
                    showNotification({
                      title: "Instance Approved",
                      message: resp.detail.msg
                    })
                  })
                }}>Approve</Button>
                <Button variant="outline" onClick={() => {
                  DenyInstanceRequest(payload.username, hostname as string, payload.type as Cloud.Type, token as string).then((resp) => {
                    showNotification({
                      title: "Instance Denied",
                      message: resp.detail.msg
                    })
                  })
                }}> Deny</Button>
              </nav>
            </section>
          ) : (<></>)}
        </div>
      </Modal>
    </>
  )
}

export default InstanceApproval;
