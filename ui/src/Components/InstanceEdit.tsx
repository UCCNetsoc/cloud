import { ActionIcon, Anchor, Button, createStyles, Loader, Modal, ScrollArea, Table, Text, Tooltip, useMantineTheme } from "@mantine/core";
import { showNotification } from "@mantine/notifications";
import { IconAlertCircle, IconAlertTriangle, IconExternalLink, IconInfoCircle, IconPlus, IconTrash } from "@tabler/icons";
import { useContext, useState } from "react";
import { DeleteInstance, DeleteVhost, ResetRootPassword, ShutdownInstance, StartInstance, StopInstance } from "../api";
import { DesktopContext, UserContext } from "../App";
import { Cloud } from "../types";
import PortModal from "./PortModal";
import ResourceRing from "./ResourceRing";
import VhostModal from "./VhostModal";

const useStyles = createStyles((theme) => ({
  header: {
    position: 'sticky',
    top: 0,
    backgroundColor: theme.colorScheme === 'dark' ? theme.colors.dark[7] : theme.white,
    transition: 'box-shadow 150ms ease',
    zIndex: 100,

    '&::after': {
      content: '""',
      position: 'absolute',
      left: 0,
      right: 0,
      bottom: 0,
      borderBottom: `1px solid ${theme.colorScheme === 'dark' ? theme.colors.dark[3] : theme.colors.gray[2]
        }`,
    },
  },

  scrolled: {
    boxShadow: theme.shadows.sm,
  },
}));

const InstanceEdit = (props: { instance: Cloud.Instance }) => {
  const [remarks, setRemarks] = useState<string[] | null>(null);
  const [vhostScrolled, setVhostScrolled] = useState(false);
  const [portScrolled, setPortScrolled] = useState(false);

  const [vhostOpen, setVhostOpen] = useState(false);
  const [portOpen, setPortOpen] = useState(false);
  const { classes, cx } = useStyles();
  const theme = useMantineTheme();
  const desktop = useContext(DesktopContext);

  const actions = [
    {
      label: "Start",
      disabled: false,
      onClick: async () => {
        StartInstance(props.instance.hostname, props.instance.type).then((resp) => {
          showNotification({
            title:
              <span style={{ display: "flex", alignItems: "center", }}>
                <Loader sx={{ margin: "0 1em" }} /> <span>Starting instance {props.instance.hostname}</span>
              </span>,
            autoClose: 3000,
            message: "Started instance"
          })
        }).catch((e) => {
          console.log(e)
          showNotification({
            title:
              <span style={{ display: "flex", alignItems: "center", }}>
                <IconAlertTriangle /> <span style={{ margin: "0 1em" }}>Failed to start instance {props.instance.hostname}, may already be running</span>
              </span>,
            autoClose: 3000,
            message: undefined
          })
        })
      },
      color: "green.9",
    },
    {
      label: "Terminal",
      disabled: props.instance?.status !== Cloud.Status.Running,
      onClick: () => {
        window.open(`https://ssh.netsoc.cloud/ssh/host/${props.instance?.metadata.network.nic_allocation.addresses[0].split("/")[0]}`, "_blank");
      }
    },
    {
      label: "Shutdown",
      disabled: false,
      onClick: () => {
        ShutdownInstance(props.instance.hostname, props.instance.type).then((resp) => {
          showNotification({
            title:
              <span style={{ display: "flex", alignItems: "center", }}>
                <Loader sx={{ margin: "0 1em" }} /> <span>Shutting down instance {props.instance.hostname}</span>
              </span>,
            message: undefined
          })
        }).catch((e) => {
          console.log(e)
          showNotification({
            title:
              <span style={{ display: "flex", alignItems: "center", }}>
                <IconAlertTriangle /> <span style={{ margin: "0 1em" }}>Failed to shutdown instance {props.instance.hostname}</span>
              </span>,
            message: "If issues persist, ask for help in netsoc-cloud channel on Discord."
          })
        })
      },
      color: "orange"
    },
    {
      label: "Reset Root Password",
      disabled: props.instance?.status !== Cloud.Status.Running,
      onClick: () => {
        ResetRootPassword(props.instance.hostname, props.instance.type as Cloud.Type).then((resp) => {
          showNotification({
            title: "Reset Root User",
            message: resp.detail.msg
          })
        })
      },
      color: "grape.6",
    },
    {
      label: "Delete",
      disabled: false,
      onClick: () => {
        ShutdownInstance(props.instance.hostname, props.instance.type).then(() => {
          DeleteInstance(props.instance.hostname, props.instance.type as Cloud.Type).then((resp) => {
            showNotification({
              title: "Deleted Instance",
              message: resp.detail.msg
            })
          })
        })
      },
      color: "red.8"
    }
  ]

  const possible_remarks = props.instance ? Object.values(props.instance?.remarks) : null;
  if (possible_remarks !== null && props.instance !== null) {
    return (
      <>
        <div style={{
          padding: "0 1em",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <div style={{ minHeight: "36vh", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
            <nav style={{ height: "5vh" }}>
              <Button.Group>
                {actions.map((action, index) => (
                  <Button disabled={action.disabled} size="xs" color={action.color} onClick={action.onClick} key={index}>
                    {action.label}
                  </Button>
                ))}
              </Button.Group>
              {(props.instance.status !== Cloud.Status.Running) ? <small>* Some actions are unavailable while instance isn't running.</small> : null}
            </nav>
            <section style={{ height: "20vh", fontSize: "0.8em" }}>
              <h1 style={{ fontSize: "1em", margin: "0.6em 0 0.2em 0" }}>Details</h1>
              <Table verticalSpacing="xs">
                <tbody>
                  <tr
                    style={{
                      height: "2em",
                    }}
                  >
                    <td>
                      Hostname
                    </td>
                    <td>
                      {props.instance.hostname}
                    </td>
                  </tr>
                  <tr>
                    <td>
                      Template
                    </td>
                    <td>{
                      props.instance.metadata?.template_metadata ? props.instance.metadata?.template_metadata?.title : "N/A"
                    }
                    </td>
                  </tr>
                  <tr>
                    <td>
                      Memory
                    </td>
                    <td>
                      {props.instance.specs.memory / 1024}G
                    </td>
                  </tr>
                  <tr>
                    <td>
                      CPU Cores
                    </td>
                    <td>
                      {props.instance.specs.cores}
                    </td>
                  </tr>
                </tbody>
              </Table>
            </section>
            <div style={{ height: "30vh" }}>
              <h1 style={{ fontSize: "1em", margin: "1.4em 0 0 0" }}>VHosts</h1>

              <ScrollArea sx={{ height: 200 }} onScrollPositionChange={({ y }) => setVhostScrolled(y !== 0)}>
                <Table verticalSpacing="xs">
                  <thead className={cx(classes.header, { [classes.scrolled]: vhostScrolled })}>
                    <tr>
                      <th></th>
                      <th style={{ whiteSpace: "nowrap" }}>
                        <Tooltip label="Domain name. You can choose a domain like *.netsoc.cloud or your own custom domain.">
                          <span>Domain <IconInfoCircle size={14} /></span>
                        </Tooltip>
                      </th>
                      <th style={{ whiteSpace: "nowrap" }}>
                        <Tooltip multiline label="Managed SSL: we will handle all SSL cert requirements.">
                          <span>Managed SSL <IconInfoCircle size={14} /></span>
                        </Tooltip>
                      </th>
                      <th style={{ whiteSpace: "nowrap" }}>
                        <Tooltip multiline label="Port that your service is running on in the instance (generally 80 or 8080).">
                          <span>Internal Port <IconInfoCircle size={14} /></span>
                        </Tooltip>
                      </th>
                      <th>
                        <Button leftIcon={<IconPlus />} onClick={() => { setVhostOpen(true) }}>
                          Add New
                        </Button>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {
                      Object.values(props.instance.metadata.network.vhosts).length > 0 ?
                        (Object.values(props.instance.metadata.network.vhosts).map((vhost, index) => {
                          const vhost_link = Object.keys(props.instance.metadata.network.vhosts)[index]
                          const relevant_remarks = possible_remarks.filter((remark) => { return remark.includes(vhost_link) })
                          return (
                            <tr key={index}>
                              {relevant_remarks.length > 0 ? (
                                <td>
                                  <ActionIcon style={{ zIndex: "1" }} color="red.7" onClick={() => { setRemarks(possible_remarks) }}>
                                    <IconAlertTriangle size={22} />
                                  </ActionIcon>
                                </td>) : (<td></td>)
                              }
                              <td><Anchor target="_blank" href={`${vhost.https || vhost.port == 443 ? "https://" : "http://"}${vhost_link}`}>{vhost_link}</Anchor> <IconExternalLink size={16} /> </td>
                              <td>{vhost.https ? 'No' : 'Yes'}</td>
                              <td>{vhost.port}</td>
                              <td>
                                <ActionIcon variant="subtle" color="red.6" onClick={() => {
                                  showNotification({
                                    title: "Deleting VHost",
                                    message: undefined,
                                    color: "red.6"
                                  })

                                  DeleteVhost(props.instance.type, props.instance.hostname, vhost_link).then((status_code) => {
                                    showNotification({
                                      title: "Deleted VHost",
                                      message: status_code,
                                      color: "red.6"
                                    })
                                  })
                                }}>
                                  <IconTrash size={18} />
                                </ActionIcon>
                              </td>
                            </tr>
                          )
                        })
                        ) : (
                          <tr>
                            <td colSpan={5} style={{ textAlign: "center" }}>
                              No VHosts
                            </td>
                          </tr>
                        )
                    }
                  </tbody>
                </Table>
              </ScrollArea>
            </div>
            <>
              <h1 style={{ fontSize: "1em", marginTop: 0 }}>TCP/UDP Ports</h1>
              <ScrollArea sx={{ height: 200 }} onScrollPositionChange={({ y }) => setPortScrolled(y !== 0)}>
                <Table verticalSpacing="xs">
                  <thead className={cx(classes.header, { [classes.scrolled]: portScrolled })}>
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
                      <th>
                        <Button leftIcon={<IconPlus />} onClick={() => { setPortOpen(true) }}>
                          Add New
                        </Button>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {
                      Object.keys(props.instance.metadata.network.ports).length > 0 ?
                        (Object.keys(props.instance.metadata.network.ports).map((port, index) => (
                          <tr key={index}>
                            <td>{port}</td>
                            <td>{props.instance.metadata.network.ports[parseInt(port)]}</td>
                            <td>
                              <ActionIcon variant="subtle" color="red.6">
                                <IconTrash size={18} />
                              </ActionIcon>
                            </td>
                          </tr>
                        ))) :
                        (
                          <tr>
                            <td style={{ textAlign: "center" }} colSpan={3}>No ports</td>
                          </tr>
                        )}
                  </tbody>
                </Table>
              </ScrollArea>
            </>
          </div>
          <div style={{ display: "flex" }}>
            <div style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}>
              <ResourceRing current={props.instance.mem} max={props.instance.specs.memory * 10000} size={100} longlabel={(props.instance.specs.memory / 1000).toString() + 'G'} />
              <Text>Memory</Text>
            </div>
            {props.instance.type === Cloud.Type.LXC && (
              <div style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}>
                <ResourceRing current={props.instance.disk} max={props.instance.specs.disk_space * 10000000} size={100} longlabel={props.instance.specs.disk_space.toString() + 'G'} />
                <Text>Storage</Text>
              </div>
            )}
          </div>
        </div>
        <Modal
          sx={{ overflowX: "hidden" }}
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
        <Modal fullScreen={!desktop} sx={{ padding: "2em" }} size="lg" centered opened={vhostOpen} onClose={() => { setVhostOpen(false) }}>
          <VhostModal instance={props.instance} />
        </Modal>
        <Modal fullScreen={!desktop} sx={{ padding: "2em" }} size="lg" centered opened={portOpen} onClose={() => { setPortOpen(false) }}>
          <PortModal instance={props.instance} />
        </Modal>
      </>
    )
  }
  else return (<></>)
}

export default InstanceEdit;
