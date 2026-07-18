<?php
/**
 * Plugin Name: organic-os bridge
 * Description: Registers RankMath SEO meta + agent_jsonld for the REST API so
 * organic-os can read/write them with an Application Password, and renders
 * agent_jsonld into wp_head. Install as an mu-plugin (wp-content/mu-plugins/).
 * Version: 0.1.0
 * License: MIT
 */

add_action('init', function () {
    $keys = ['rank_math_title', 'rank_math_description',
             'rank_math_canonical_url', 'rank_math_focus_keyword', 'agent_jsonld'];
    foreach ($keys as $key) {
        register_post_meta('', $key, [
            'show_in_rest'  => true,
            'single'        => true,
            'type'          => 'string',
            'auth_callback' => function ($allowed, $meta_key, $post_id) {
                return current_user_can('edit_post', $post_id);
            },
        ]);
    }
});

add_action('wp_head', function () {
    if (!is_singular()) return;
    $jsonld = get_post_meta(get_the_ID(), 'agent_jsonld', true);
    if (!$jsonld) return;
    json_decode($jsonld);
    if (json_last_error() !== JSON_ERROR_NONE) return; // never render invalid JSON
    echo '<script type="application/ld+json">' . $jsonld . '</script>' . "\n";
});
