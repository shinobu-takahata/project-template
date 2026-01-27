FROM public.ecr.aws/aws-observability/aws-for-fluent-bit:3.0.0

# Copy custom configuration files to a separate directory
COPY fluent-bit.conf /fluent-bit/custom/fluent-bit.conf
COPY parsers.conf /fluent-bit/custom/parsers.conf

# Health check endpoint (Fluent Bit exposes metrics on port 2020 by default)
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:2020/api/v1/health || exit 1
