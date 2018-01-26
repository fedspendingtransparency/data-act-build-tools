SELECT COUNT(*)
  FROM cwd_user
  JOIN cwd_user_attributes ON cwd_user_attributes.user_id = cwd_user.id
                           AND cwd_user_attributes.attribute_name = 'login.lastLoginMillis'
                           AND cwd_user_attributes.attribute_value <= CAST((extract(epoch from now()) - 10368000) * 1000 AS text)
  WHERE cwd_user.active = 1;

UPDATE cwd_user
  SET active = 0
  WHERE id IN (SELECT cwd_user_attributes.user_id
                 FROM cwd_user_attributes
                 WHERE cwd_user_attributes.attribute_name = 'login.lastLoginMillis'
                 AND cwd_user_attributes.attribute_value <= CAST((extract(epoch from now()) - 10368000) * 1000 AS text))
  AND active = 1;