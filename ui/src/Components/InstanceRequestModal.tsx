import { Box, Button, ScrollArea, Text, Textarea, TextInput, useMantineTheme } from "@mantine/core";
import { useForm } from "@mantine/form";
import { showNotification } from "@mantine/notifications";
import { IconArrowRight } from "@tabler/icons";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CreateInstanceRequest } from "../api/instance_request";
import { Cloud } from "../types";
import ModalTop from "./ModalTop";

const InstanceRequestModal = (props: { templates: Cloud.Template[][] | null }) => {
  const [metaData, setMetaData] = useState<Cloud.TemplateMetadata | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<Cloud.Template | null>(null);
  const [selectedTemplateType, setSelectedTemplateType] = useState<Cloud.Type | null>(null);

  const theme = useMantineTheme()
  const navigate = useNavigate()

  const defaultDetail = {
    title: "Select a template to continue",
    subtitle: "A template represents a base installation for your new instance."
  }

  const form = useForm<{ template_id: string, hostname: string, reason: string, }>({
    initialValues: {
      template_id: "",
      hostname: "",
      reason: "",
    },
    validate: (values) => ({
      hostname: /^[a-zA-Z0-9]+$/.test(values.hostname) ? null : "Alphanumeric with hyphens allowed only.",
      reason: values.reason.length > 0 ? null : "Must give a reason",
      template_id: null
    })
  })

  return (
    <>
      <div>
        <ModalTop />
        <div style={{ display: "flex", alignItems: "center", paddingTop: "18px", width: "800px" }}>
          <ScrollArea style={{ height: "600px", width: "400px", borderRight: `1px solid ${theme.colorScheme === "dark" ? "white" : "black"}` }}>
            {props.templates?.map((templates, typeIndex) => {
              return templates.map((template, index) => {
                return (
                  <div key={`${typeIndex}.${index}`}>
                    <Box
                      key={index}
                      sx={(theme) => ({
                        backgroundColor: theme.colorScheme === 'dark' ? props.templates ? selectedTemplate === props.templates[typeIndex][index] ? theme.colors.dark[4] : theme.colors.dark[7] : theme.colors.gray[0] : "unset",
                        padding: theme.spacing.xl,
                        borderRadius: theme.radius.md,
                        cursor: 'pointer',
                        width: "100%",

                        '&:hover': {
                          backgroundColor:
                            theme.colorScheme === 'dark' ? theme.colors.dark[5] : theme.colors.gray[1],
                        },
                      })}
                      onClick={() => {
                        setMetaData(template.metadata);
                        setSelectedTemplate(template);
                        setSelectedTemplateType([Cloud.Type.LXC, Cloud.Type.VPS][typeIndex])
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "flex-start", fontSize: "0.9em" }}>
                        <img src={template.metadata.logo_url} style={{ maxWidth: "32px", marginRight: "1em" }} />
                        <div>
                          <span style={{ fontSize: "1.1em", display: "block" }}>{template.metadata.title}</span>
                          <span style={{ opacity: "60%" }}>{template.metadata.subtitle}</span>
                        </div>
                      </div>
                      {/* <small style={{ display: "block" }}>{template.specs.cores} CPU, {template.specs.memory} RAM, {template.specs.disk_space}GB Disk</small> */}
                    </Box>
                  </div>
                )
              })
            })}

          </ScrollArea>
          <ScrollArea type="always" style={{ height: "600px", width: "600px", padding: "1em" }}>
            {metaData ? (
              <div style-={{ width: "300px" }}>
                <div style={{ display: "flex", alignItems: "center" }}>
                  <img style={{ height: "64px", marginRight: "2em" }} src={metaData?.logo_url} alt={`Icon for ${metaData?.title}`} />
                  <div>
                    <Text size="xl">{metaData?.title}</Text>
                    <Text size="sm">{selectedTemplate?.specs.cores} CPU, {selectedTemplate?.specs.memory} RAM, {selectedTemplate?.specs.disk_space}GB Disk</Text>
                  </div>
                </div>
                <Text>{metaData?.subtitle}</Text>

                <p style={{ whiteSpace: "pre-wrap" }}>
                  {metaData?.description}
                </p>

                <form
                  onSubmit={form.onSubmit((values) => {
                    try {
                      CreateInstanceRequest(selectedTemplateType ? selectedTemplateType : Cloud.Type.LXC, values.hostname, selectedTemplate?.hostname ? selectedTemplate?.hostname : "", values.reason).then((item) => {
                        showNotification({
                          title: "Requested Instance",
                          message: item.detail.msg
                        })
                        navigate("/instances")
                      })
                    } catch {
                      showNotification({
                        title: "Instance Request Failed",
                        message: "See the netsoc-cloud channel on Discord and ask a sysadmin for more info."
                      })
                    }
                  })}
                  style={{ padding: "0 2em 0 1em", margin: "2em auto" }}>
                  <TextInput type="text" {...form.getInputProps("hostname")} style={{ width: "100%", maxWidth: "300px", marginBottom: "2em" }} label="Hostname" placeholder="hostname" rightSection={<p style={{ width: "100px", whiteSpace: "nowrap" }}>.netsoc.cloud</p>} />
                  <Textarea {...form.getInputProps("reason")} label="Why do you want this instance?" minRows={6}></Textarea>
                  <div style={{ margin: "1em auto", display: "flex", flexDirection: "row-reverse" }}>
                    <Button type="submit" leftIcon={<IconArrowRight />}>
                      Submit
                    </Button>
                  </div>
                </form>
              </div>
            ) : (
              <>
                <Text size="lg" >{defaultDetail.title}</Text>
                <Text>{defaultDetail.subtitle}</Text>
              </>
            )}
          </ScrollArea>

        </div>
      </div>
    </>
  )
}

export default InstanceRequestModal;
