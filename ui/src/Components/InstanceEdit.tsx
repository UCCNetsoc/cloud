import { ActionIcon, Anchor, Button, Loader, Modal, Table, Text, Tooltip, useMantineTheme } from "@mantine/core";
import { showNotification } from "@mantine/notifications";
import { IconAlertCircle, IconAlertTriangle, IconExternalLink, IconInfoCircle, IconPlus, IconTrash } from "@tabler/icons";
import { useState } from "react";
import { MarkInstanceActive, StartInstance, StopInstance } from "../api";
import { Cloud } from "../types";
import ResourceRing from "./ResourceRing";

const InstanceEdit = (props: { instance: Cloud.Instance }) => {
  const [remarks, setRemarks] = useState<string[] | null>(null);

  const theme = useMantineTheme();

  const actions = [
    {
      label: "Start",
      onClick: async () => {
        const resp = await StartInstance(props.instance.hostname, props.instance.type);
        if (resp) {
          showNotification({
            title:
              <span style={{ display: "flex", alignItems: "center", }}>
                <Loader sx={{ margin: "0 1em" }} /> <span>Starting instance {props.instance.hostname}</span>
              </span>,
            autoClose: 3000,
            message: undefined
          })
        } else {
          showNotification({
            title:
              <span style={{ display: "flex", alignItems: "center", }}>
                <IconAlertTriangle /> <span style={{ margin: "0 1em" }}>Failed to start instance {props.instance.hostname}</span>
              </span>,
            autoClose: 3000,
            message: undefined
          })
        }
      },
      color: "green.9",
    },
    {
      label: "Reboot",
      onClick: () => {
        // RebootInstance()
      },
      color: "yellow.7"
    },
    {
      label: "Stop",
      onClick: async () => {
        const resp = await StopInstance(props.instance.hostname, props.instance.type)
        if (resp) {
          showNotification({
            title:
              <span style={{ display: "flex", alignItems: "center", }}>
                <Loader sx={{ margin: "0 1em" }} /> <span>Stopping instance {props.instance.hostname}</span>
              </span>,
            autoClose: 3000,
            message: undefined
          })
        }
      },
      color: "orange"
    },
    {
      label: "Reactivate",
      onClick: () => {
        MarkInstanceActive(props.instance.hostname, props.instance.type);
      }
    },
    {
      label: "Reset Password",
      onClick: () => {
        // ResetPassword()
      },
      color: "grape.6",
    },
    {
      label: "Delete",
      onClick: () => {
        // DeleteInstance()
      },
      color: "red.8"
    }
  ]

  const possible_remarks = Object.keys(props.instance.remarks);

  return (
    <>
      <div style={{
        position: "absolute",
        top: "0",
        right: "0",
        padding: "2em 1em",
        height: "100vh",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "space-between",
        border: "1px solid",
        borderColor: props.instance.status === "Running" ? "green" : "red",
      }}>
        <div style={{ minHeight: "40vh", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <nav>
            {actions.map((action, index) => (
              <Button size="xs" color={action.color} onClick={action.onClick} style={{ margin: "0.4em 0.6em" }} key={index}>
                {action.label}
              </Button>
            ))}
          </nav>
          <>
            <h1 style={{ fontSize: "1.4em", margin: "0.6em 0 0.2em 0" }}>Details</h1>
            <Table verticalSpacing="md">
              <tbody>
                <tr
                  style={{
                    height: "2em",
                  }}
                >
                  <td>Hostname</td>
                  <td>
                    {props.instance.hostname}
                  </td>
                </tr>
                <tr>
                  <td>CPU Cores</td>
                  <td>
                    {props.instance.specs.cores}
                  </td>
                </tr>
                <tr>
                  <td>Memory</td>
                  <td>
                    {props.instance.specs.memory / 1024}G
                  </td>
                </tr>
              </tbody>
            </Table>
          </>
          <>
            <h1 style={{ fontSize: "1.4em", margin: "0.6em 0 0.2em 0" }}>VHosts</h1>
            <Table verticalSpacing="xs">
              <thead>
                <tr>
                  <th></th>
                  <th style={{ whiteSpace: "nowrap" }}>
                    <Tooltip label="Domain name. You can choose a domain like *.netsoc.cloud or your own custom domain.">
                      <span>Domain <IconInfoCircle size={14} /></span>
                    </Tooltip>
                  </th>
                  <th style={{ whiteSpace: "nowrap" }}>
                    <Tooltip multiline label="Managed SSL means we will handle all SSL cert requirements for you. Then, you can access your service using https.">
                      <span>Managed SSL <IconInfoCircle size={14} /></span>
                    </Tooltip>
                  </th>
                  <th style={{ whiteSpace: "nowrap" }}>
                    <Tooltip multiline label="Port that your service is running on in the instance (generally 80 or 8080).">
                      <span>Internal Port <IconInfoCircle size={14} /></span>
                    </Tooltip>
                  </th>
                  <th>
                    <span>
                      <ActionIcon>
                        <IconPlus />
                      </ActionIcon> Add new </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {
                  Object.values(props.instance.metadata.network.vhosts).map((vhost, index) => {
                    const vhost_link = Object.keys(props.instance.metadata.network.vhosts)[index]

                    const relevant_remarks = props.instance.remarks.filter((remark) => { return remark.includes(vhost_link) })
                    return (
                      <tr key={index}>
                        {relevant_remarks.length > 0 ? (
                          <td>
                            <ActionIcon color="red.7" onClick={() => { setRemarks(props.instance.remarks) }}>
                              <IconAlertTriangle size={22} />
                            </ActionIcon>
                          </td>) : (<td></td>)
                        }
                        <td><Anchor target="_blank" href={vhost_link}>{vhost_link}</Anchor> <IconExternalLink size={16} /> </td>
                        <td>{vhost.https ? 'No' : 'Yes'}</td>
                        <td>{vhost.port}</td>
                        <td>
                          <ActionIcon variant="subtle" color="red.6">
                            <IconTrash size={18} />
                          </ActionIcon>
                        </td>
                      </tr>
                    )
                  })}
              </tbody>
            </Table>
          </>
          <>
            <h1 style={{ fontSize: "1.4em", margin: "0.6em 0 0.2em 0" }}>TCP Ports</h1>
            <Table verticalSpacing="xs" title="TCP Ports">
              <thead>
                <tr>
                  <th style={{ whiteSpace: "nowrap" }}>
                    <Tooltip label="Port accessible by internet.">
                      <span>External Port <IconInfoCircle size={14} /></span>
                    </Tooltip>
                  </th>
                  <th style={{ whiteSpace: "nowrap" }}>
                    <Tooltip multiline label="Port that your service is running on in the instance (example 22 for SSH).">
                      <span>Internal Port <IconInfoCircle size={14} /></span>
                    </Tooltip>
                  </th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {Object.keys(props.instance.metadata.network.ports).map((port, index) => (
                  <tr key={index}>
                    <td>{port}</td>
                    <td>{props.instance.metadata.network.ports[parseInt(port)]}</td>
                    <td>
                      <ActionIcon variant="subtle" color="red.6">
                        <IconTrash size={18} />
                      </ActionIcon>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </>
        </div>
        <div style={{ display: "flex" }}>
          <div style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}>
            <ResourceRing current={props.instance.mem} max={props.instance.specs.memory * 10000} size={120} longlabel={(props.instance.specs.memory / 1000).toString() + 'G'} />
            <Text>Memory</Text>
          </div>
          {props.instance.type === Cloud.Type.LXC && (
            <div style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}>

              <ResourceRing current={props.instance.disk} max={props.instance.specs.disk_space * 10000000} size={120} longlabel={props.instance.specs.disk_space.toString() + 'G'} />
              <Text>Storage</Text>
            </div>
          )}
        </div>
      </div >
      <Modal
        opened={remarks !== null}
        onClose={() => setRemarks(null)}
        title="DNS Remarks"
        centered
        overlayColor={theme.colorScheme === 'dark' ? theme.colors.dark[9] : theme.colors.gray[2]}
        size="45%"
      >
        {remarks?.map((remark, index) => (
          <div key={index} style={{ margin: "1em", display: "flex", alignItems: "center" }}>
            <IconAlertCircle style={{ margin: "0.6em" }}></IconAlertCircle><Text>{remark}</Text>
          </div>
        ))}

        <Text style={{ margin: "2.4em 1em 1em 1em" }} >DNS records can take some time to propagate, but if issues persist or you are confused, please ask the sysadmins in the <pre style={{ display: "inline" }}>#netsoc-cloud</pre> channel on the <Anchor>Discord</Anchor></Text>
      </Modal>
    </>
  )
}

export default InstanceEdit;
