<?php
/**
 * MU-Plugin: SEO Schema JSON-LD Output
 *
 * Reads the '_seo_schema_json_ld' meta field from posts and outputs
 * the schema markup as <script type="application/ld+json"> in wp_head.
 *
 * Installation:
 *   Copy this file to: wp-content/mu-plugins/mu-seo-schema.php
 *
 * The Fabrica de Artigos SEO pipeline sends schema data via REST API
 * as a post meta field. This plugin renders it in the HTML head.
 */

// Register the meta field so it can be set via REST API
add_action('init', function () {
    register_post_meta('post', '_seo_schema_json_ld', [
        'show_in_rest' => true,
        'single'       => true,
        'type'         => 'string',
        'auth_callback' => function () {
            return current_user_can('edit_posts');
        },
    ]);
});

// Output schema JSON-LD in wp_head for single posts
add_action('wp_head', function () {
    if (!is_singular('post')) {
        return;
    }

    $schema_json = get_post_meta(get_the_ID(), '_seo_schema_json_ld', true);
    if (empty($schema_json)) {
        return;
    }

    $schemas = json_decode($schema_json, true);
    if (!is_array($schemas)) {
        return;
    }

    foreach ($schemas as $schema) {
        if (!empty($schema)) {
            $encoded = wp_json_encode($schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
            if ($encoded) {
                echo '<script type="application/ld+json">' . "\n" . $encoded . "\n" . '</script>' . "\n";
            }
        }
    }
}, 1);
